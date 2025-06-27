import os
import sys

msg = sys.argv[1] if len(sys.argv) == 2 else "使用 True 或者 False 对应 is not null 和 is null"

cmd1 = "git add ."
cmd2 = 'git commit -m "{}"'.format(msg)
cmd3 = "git push"

os.system(cmd1)
os.system(cmd2)
os.system(cmd3)
