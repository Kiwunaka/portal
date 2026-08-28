# Third-party notices

The server binary is built with Go and the pinned `github.com/miekg/dns`
module. Depending on the selected platform, the module graph also includes Go
supplementary modules under `golang.org/x/`. Their BSD licenses are retained in
`LICENSES/`.

The exact compiled dependency versions and hashes belong to the generated
bundle manifest. Test-only modules are present in `go.sum` but are not described
as compiled binary dependencies unless the Go build metadata reports them.
