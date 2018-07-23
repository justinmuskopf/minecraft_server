from subprocess import Popen, PIPE, call

proc = Popen(["netstat", "-lnp"], stdout = PIPE)
stdout, stderr = proc.communicate()

if "java" and "25565" in stdout:
    print "Server is up!"
else:
    print "Server is down!"
