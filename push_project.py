import os
import sys

msg = sys.argv[1] if len(sys.argv) == 2 else "自动提交"

cmd1 = "git add ."
cmd2 = 'git commit -m "{}"'.format(msg)
cmd3 = "git push"

os.system(cmd1)
os.system(cmd2)
os.system(cmd3)
