import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/scripts')
import remote_run_owned_awg_core_interop as interop
root=Path(__file__).parent
git=Path('C:/Program Files/Git/cmd/git.exe')
go=Path('C:/Users/kiwun/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.8.windows-amd64/bin/go.exe')
core=Path('E:/r12core-implementation')
expected='02a091cb0e369192a5ad0909b56ccba8aa1dce17'
assert not (root/'build.json').exists()
revision=interop._exact_core_revision(git,core,expected)
module=interop._materialize_core_module(git,core,revision,root/'build')
binary=root/'owned-awg.test'
digest=interop._prepare_interop_binary(go,module,root/'build/source',binary,target='linux_arm64')
result={'core_revision':revision,'binary_sha256':digest,'binary_bytes':binary.stat().st_size,'go_sha256':interop._file_sha256(go),'git_sha256':interop._file_sha256(git),'target':'linux_arm64','interop_runner_sha256':interop._file_sha256(Path(interop.__file__))}
(root/'build.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
