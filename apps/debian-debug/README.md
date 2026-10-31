# debian-debug

Debian with networking, database and troubleshooting tools, to debug from inside a cluster: `nmap`, `tshark`, `tcpdump`, `dnsutils`, `ldnsutils`, `ldap-utils`, the MariaDB and PostgreSQL clients, `openssh-client`, and the usual editors and process tools.

Recommends are deliberately installed, unlike every other image here: this is a toolbox, and `nmap`, `tshark` and `dnsutils` pull useful companions in that way.

## It idles until you tell it to stop

```dockerfile
CMD ["sh", "-c", "trap 'exit 0' TERM INT; while [ ! -e /tmp/continue ]; do sleep 3 & wait $!; done"]
```

The container sleeps so there is something to `kubectl exec` into, and exits when `/tmp/continue` appears:

```sh
kubectl exec deploy/debian-debug -- touch /tmp/continue
```

`sleep` runs in the background with `wait` rather than in the foreground, so the shell stays responsive to signals: with a plain `sleep 3`, `SIGTERM` would not be handled until it returned, and Kubernetes would wait out the full termination grace period on every delete. The trap exits 0, so a normal stop is not reported as a failure.

The version is the date of the build, since there is no upstream release to track; the weekly rebuild is what picks up patched Debian packages behind the pinned base digest.
