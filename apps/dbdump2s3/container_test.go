package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/dbdump2s3:rolling")

	// Every tool a dump, an encryption and an upload needs: a missing one would otherwise only
	// show up on the night the backup runs
	helpers.RequireCommandSucceeds(t, image, nil, "pg_dump", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "pg_restore", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "mariadb-dump", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "age", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "gpg", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "aws", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "xz", "--version")
	helpers.RequireCommandSucceeds(t, image, nil, "curl", "--version")

	// pg_dump refuses to dump a server newer than itself, so a base image that moved backwards to
	// postgresql17-client has to fail here rather than at 03:00
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`pg_dump --version | grep -qE ' (1[89]|[2-9][0-9])\.'`)

	// Missing configuration is refused, not treated as a backup of nothing
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`out=$(/usr/local/bin/dbdump2s3 2>&1) && exit 1; echo "$out" | grep -q DUMP_KIND`)

	// An unknown ENCRYPTION is refused rather than falling back to one of them
	helpers.RequireCommandSucceeds(t, image,
		&helpers.ContainerConfig{Env: map[string]string{
			"DUMP_KIND":     "postgres",
			"DB_HOST":       "db",
			"DATABASES_CSV": "/dev/null",
			"USERS_CSV":     "/dev/null",
			"PASSWORD_DIR":  "/dev/null",
			"S3_BUCKET":     "b",
			"S3_ENDPOINT":   "https://example.invalid",
			"CLUSTER":       "c",
			"ENCRYPTION":    "rot13",
		}},
		"sh", "-c",
		`out=$(/usr/local/bin/dbdump2s3 2>&1) && exit 1; echo "$out" | grep -q "ENCRYPTION must be age or pgp"`)

	// The gpg flags the script encrypts with, round-tripped
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		export GNUPGHOME=/tmp/gnupg; mkdir -p "$GNUPGHOME"; chmod 700 "$GNUPGHOME"
		gpg --batch --quiet --passphrase "" --pinentry-mode loopback \
			--quick-generate-key backup@example.invalid default default never
		fpr=$(gpg --batch --with-colons --list-keys | awk -F: '$1 == "fpr" { print $10; exit }')
		test -n "$fpr"
		echo secret-payload > /tmp/plain
		gpg --batch --yes --no-tty --quiet -z 0 --trust-model always \
			--recipient "$fpr" --encrypt --output /tmp/plain.gpg /tmp/plain
		gpg --batch --quiet --pinentry-mode loopback --passphrase "" --decrypt /tmp/plain.gpg \
			| grep -q secret-payload`)

	// The script itself accepts a base64 public key in PGP_RECIPIENT and imports it before it
	// reaches the first database, so a bad key never gets as far as a dump
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		export GNUPGHOME=/tmp/keygen; mkdir -p "$GNUPGHOME"; chmod 700 "$GNUPGHOME"
		gpg --batch --quiet --passphrase "" --pinentry-mode loopback \
			--quick-generate-key backup@example.invalid default default never
		PGP_RECIPIENT=$(gpg --armor --export backup@example.invalid | base64 | tr -d '\n')
		unset GNUPGHOME
		printf 'name\ndb1\n' > /tmp/databases.csv
		printf 'user,database,privileges\nowner,db1,ALL\n' > /tmp/users.csv
		mkdir -p /tmp/pw /tmp/work && echo secret > /tmp/pw/owner
		export DUMP_KIND=postgres DB_HOST=db.invalid DATABASES_CSV=/tmp/databases.csv \
			USERS_CSV=/tmp/users.csv PASSWORD_DIR=/tmp/pw S3_BUCKET=b \
			S3_ENDPOINT=https://example.invalid CLUSTER=c WORKDIR=/tmp/work \
			ENCRYPTION=pgp PGP_RECIPIENT="$PGP_RECIPIENT"
		out=$(/usr/local/bin/dbdump2s3 2>&1) && exit 1
		echo "$out" | grep -q "encrypting to PGP key"`)

	// A corrupt PGP_RECIPIENT is reported as such, not swallowed by the pipeline into an empty
	// import that gpg would accept
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`printf 'name\ndb1\n' > /tmp/databases.csv
		printf 'user,database,privileges\nowner,db1,ALL\n' > /tmp/users.csv
		mkdir -p /tmp/pw /tmp/work2 && echo secret > /tmp/pw/owner
		export DUMP_KIND=postgres DB_HOST=db.invalid DATABASES_CSV=/tmp/databases.csv \
			USERS_CSV=/tmp/users.csv PASSWORD_DIR=/tmp/pw S3_BUCKET=b \
			S3_ENDPOINT=https://example.invalid CLUSTER=c WORKDIR=/tmp/work2 \
			ENCRYPTION=pgp PGP_RECIPIENT='this is not base64 !!'
		out=$(/usr/local/bin/dbdump2s3 2>&1) && exit 1
		echo "$out" | grep -q "PGP_RECIPIENT is not"`)

	// The age path end to end, likewise
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		age-keygen -o /tmp/age.key 2>/dev/null
		recipient=$(age-keygen -y /tmp/age.key)
		echo secret-payload > /tmp/plain
		age --encrypt --recipient "$recipient" --output /tmp/plain.age /tmp/plain
		age --decrypt --identity /tmp/age.key /tmp/plain.age | grep -q secret-payload`)
}
