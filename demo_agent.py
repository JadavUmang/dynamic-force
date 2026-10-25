"""Offline demonstrator: a fixed repair proposal, not an LLM agent."""
import json, subprocess, tempfile, pathlib, datetime

def run(argv, cwd):
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=15)

def main():
    with tempfile.TemporaryDirectory(prefix="loop-ai-") as tmp:
        repo=pathlib.Path(tmp)
        (repo/'calculator.py').write_text('def add(a, b):\n    return a - b\n')
        (repo/'test_calculator.py').write_text('import unittest\nfrom calculator import add\nclass TestCalc(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n')
        for cmd in (['git','init'],['git','add','.'],['git','-c','user.name=Demo','-c','user.email=demo@example.invalid','commit','-m','baseline']):
            result=run(cmd,repo)
            if result.returncode: raise RuntimeError(result.stderr)
        test=['python','-m','unittest','discover','-v']
        baseline=run(test,repo)
        print('Baseline test exit:',baseline.returncode)
        if baseline.returncode==0:
            print('No failure to repair');return
        path=repo/'calculator.py'
        original=path.read_text()
        proposal=original.replace('return a - b','return a + b')
        if proposal==original: raise RuntimeError('Expected demo code not found')
        print('Proposed patch: return a - b -> return a + b')
        if input('Apply patch? [y/N] ').strip().lower()!='y':
            print('Rejected. No files modified.');return
        path.write_text(proposal)
        result=run(test,repo)
        status='PASSED' if result.returncode==0 else 'FAILED'
        diff=run(['git','diff','--','calculator.py'],repo).stdout
        report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'baseline_exit':baseline.returncode,'validation_exit':result.returncode,'diff':diff,'test_output':result.stdout+result.stderr}
        (repo/'loop-report.json').write_text(json.dumps(report,indent=2))
        print('Status:',status,'\n',diff,'\n',report['test_output'])
        print('Demo repository (temporary):',repo)
        print('Note: demo repository is deleted when the process exits.')
if __name__=='__main__': main()
