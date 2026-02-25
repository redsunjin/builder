import subprocess
import os
import shutil

class GitManager:
    """
    Git Worktree 및 브랜치를 파이썬 subprocess를 통해 제어하는 매니저 클래스.
    GSD 병렬(Parallel) 에이전트 아키텍처 지원 목적.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
    
    def _run_cmd(self, cmd: list, cwd: str = None) -> str:
        if cwd is None:
            cwd = self.repo_path
            
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nError: {result.stderr}")
        return result.stdout.strip()
        
    def add_worktree(self, branch_name: str, target_path: str):
        """
        주어진 브랜치 이름과 타겟 경로로 새로운 Git Worktree를 생성합니다.
        브랜치가 존재하지 않으면 새로 생성(-b)합니다.
        """
        abspath = os.path.abspath(target_path)
        
        # 먼저 부모 브랜치(현재 상태) 확인
        try:
            # 브랜치가 존재하는지 확인
            self._run_cmd(['git', 'rev-parse', '--verify', branch_name])
            # 존재하면 해당 브랜치로 워크트리 생성
            self._run_cmd(['git', 'worktree', 'add', abspath, branch_name])
        except RuntimeError:
            # 존재하지 않으면 새 브랜치로 워크트리 생성
            self._run_cmd(['git', 'worktree', 'add', '-b', branch_name, abspath])
            
        return abspath

    def remove_worktree(self, target_path: str, branch_name: str = None, force: bool = True):
        """
        해당 위치의 Git Worktree를 제거하고, 필요하다면 연관된 브랜치도 함께 정리합니다.
        """
        abspath = os.path.abspath(target_path)
        
        cmd = ['git', 'worktree', 'remove']
        if force:
            cmd.append('--force')
        cmd.append(abspath)
        
        # 워크트리 제거
        try:
            self._run_cmd(cmd)
        except RuntimeError as e:
            # 만약 이미 폴더가 지워졌거나 워크트리가 연결 해제되어 에러가 날 경우 무시하거나 prune
            self._run_cmd(['git', 'worktree', 'prune'])
            if os.path.exists(abspath):
                shutil.rmtree(abspath, ignore_errors=True)
                
        # 연결된 브랜치 삭제
        if branch_name:
            try:
                # 안전하게 브랜치도 삭제 (병합이 완료되었다고 가정)
                self._run_cmd(['git', 'branch', '-D', branch_name])
            except RuntimeError:
                pass

    def commit_changes(self, worktree_path: str, message: str, file_patterns: list = ['.']):
        """
        특정 Worktree 영역 안에서 변경사항을 스테이징하고 커밋합니다.
        """
        abspath = os.path.abspath(worktree_path)
        
        # Stage files
        for pattern in file_patterns:
            self._run_cmd(['git', 'add', pattern], cwd=abspath)
            
        # Commit
        try:
            self._run_cmd(['git', 'commit', '-m', message], cwd=abspath)
        except RuntimeError as e:
            # Nothing to commit 에러인 경우 무시
            if "nothing to commit" not in str(e):
                raise e

    def merge_branch(self, branch_name: str, allow_unrelated: bool = False):
        """
        현재 컨텍스트(메인 Worktree)로 지정된 브랜치를 병합(merge)합니다.
        Composition Agent가 메인 디렉토리 영역에서 최종적으로 호출합니다.
        """
        cmd = ['git', 'merge', '--no-ff', '-m', f"Merge {branch_name} into main", branch_name]
        if allow_unrelated:
            cmd.append('--allow-unrelated-histories')
            
        try:
            result = self._run_cmd(cmd)
            return True, result
        except RuntimeError as e:
            # 충돌 발생 시
            if "Merge conflict" in str(e) or "Automatic merge failed" in str(e):
                 # 향후 Composition Agent가 여기 개입하여 파일 정리
                 return False, str(e)
            else:
                 raise e

# 직접 모듈 테스트 실행용 (필요시)
if __name__ == '__main__':
    gm = GitManager()
    print("GitManager initialized.")
