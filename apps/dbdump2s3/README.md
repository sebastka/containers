# dbdump2s3

Logical backups of PostgreSQL and MariaDB servers. One dump per database, encrypted to an age or
PGP recipient, uploaded to an S3-compatible bucket.

- age: https://github.com/FiloSottile/age
- GnuPG: https://gnupg.org/documentation/
- Alpine `postgresql18-client`: https://pkgs.alpinelinux.org/package/v3.24/main/x86_64/postgresql18-client
- Alpine `mariadb-client`: https://pkgs.alpinelinux.org/package/v3.24/main/x86_64/mariadb-client

## What it does, and why

**Logs in as each database's owner, never as the superuser.** Owner passwords are re-applied on
every provisioning run, so they survive a regenerated Secret. A superuser password is only read at
initdb and drifts silently once its Secret is recreated — a backup job using it fails on a night
nobody is watching.

**Reads the same CSVs that create the databases**, so a database added there is backed up without
anyone remembering to add it here. It refuses to run against an empty list rather than reporting a
successful backup of nothing.

**Encrypts with a public key**, age or PGP, whichever `ENCRYPTION` selects. The half that can
decrypt lives outside the cluster, so a compromised pod can write backups it cannot read back.

**Verifies before uploading** — `pg_restore --list` for PostgreSQL, `xz -t` for MariaDB — and sends
its heartbeat only once every database in the list has landed in the bucket. A push monitor
watching that URL therefore catches "the job silently stopped running", not just "the job failed".

## Configuration

| Variable | Required | Meaning |
| -------- | -------- | ------- |
| `DUMP_KIND` | yes | `postgres` or `mariadb` |
| `DB_HOST` | yes | the server |
| `DB_PORT` | no | defaults to 5432 / 3306 |
| `DATABASES_CSV`, `USERS_CSV` | yes | the mounted CSVs; a header row, then `name,...` and `user,database,privileges` |
| `PASSWORD_DIR` | yes | directory holding one file per role, named after the role |
| `ENCRYPTION` | no | `age` (default) or `pgp` |
| `AGE_RECIPIENT` | if `age` | the age **public** key |
| `PGP_RECIPIENT` | if `pgp` | the armored PGP **public** key, base64 |
| `S3_BUCKET`, `S3_ENDPOINT` | yes | destination |
| `CLUSTER` | yes | used in the object key |
| `WORKDIR` | no | scratch space, defaults to `/tmp` |
| `HEARTBEAT_URL` | no | fetched once, only on complete success |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | yes | a key scoped to the backup bucket alone |

Only the chosen scheme's variable is required, so neither consumer has to set the other's. The
default is `age`, which is what this image did before it could do PGP.

With `pgp`, the key is imported once at start-up into a keyring under `WORKDIR` — a bad or missing
key fails the run rather than every database in turn — and dumps are encrypted to its
**fingerprint**, so `--recipient` cannot resolve to some other key. Output is binary, not armored,
and `-z 0` skips gpg's compression because the dumps are already compressed.

`PGP_RECIPIENT` is base64 so that an armored key, which is many lines, survives as one environment
variable. It holds the public key only; base64 is an encoding, not a second layer of protection,
and the value is as readable as the key itself:

```sh
gpg --armor --export backup@example.com | base64 -w0
```


Object keys:

```
daily/<cluster>/<kind>/<database>/YYYY-MM-DD.<ext>.<enc>
monthly/<cluster>/<kind>/<database>/YYYY-MM.<ext>.<enc>     # written on the 1st
```

`<ext>` is `dump` for PostgreSQL (custom format) and `sql.xz` for MariaDB. `<enc>` is `age` or
`gpg`. Retention belongs to the bucket's lifecycle rules, not to this image.

## Restoring

```sh
aws --endpoint-url "$S3_ENDPOINT" s3 cp "s3://$BUCKET/daily/<cluster>/postgres/<db>/2026-10-18.dump.age" .

age --decrypt --identity age.key --output db.dump 2026-10-18.dump.age   # ENCRYPTION=age
gpg --decrypt --output db.dump 2026-10-18.dump.gpg                      # ENCRYPTION=pgp

# The dump carries no roles or grants: recreate them first, then
pg_restore --host=… --username=<owner> --dbname=<db> --no-owner db.dump
```

For MariaDB, pipe the decryption through `xz -d` into `mariadb --host=… --user=…`. That dump is
written with `--databases`, so it recreates the database itself.

## Pinning

The base image is pinned by tag and digest. The apk packages deliberately are not: an Alpine branch
carries one version of each package and drops it as soon as a patched one replaces it, so
`age=1.3.1-r6` would turn a security update into a failed build. The base digest is the pin, and
Renovate bumping it is what pulls patched packages in.

Alpine 3.24 is a floor, not a preference. `pg_dump` refuses to dump a server newer than itself;
3.22 tops out at `postgresql17-client` and 3.23 was the first branch with `postgresql18-client`.
`container_test.go` asserts the client is 18 or newer so a base image moving backwards fails the
build instead of the backup.
