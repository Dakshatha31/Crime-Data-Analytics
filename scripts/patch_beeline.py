import subprocess
from pathlib import Path

# Read beeline.sh from WSL
res = subprocess.run(["wsl", "-e", "cat", "/opt/hive/bin/ext/beeline.sh"], capture_output=True, text=True)
content = res.stdout

if "--enable-preview" not in content:
    target = 'export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS'
    replacement = 'export HADOOP_CLIENT_OPTS="--enable-preview -Dorg.jline.terminal.dumb=true $HADOOP_CLIENT_OPTS'
    if target in content:
        new_content = content.replace(target, replacement, 1)
        # Write back to WSL
        p = Path("scripts/beeline_patched.sh")
        p.write_text(new_content)
        subprocess.run(["wsl", "-e", "bash", "-c", "cp /mnt/d/projects/Crime_Analytics_BDC/scripts/beeline_patched.sh /opt/hive/bin/ext/beeline.sh && chmod +x /opt/hive/bin/ext/beeline.sh"])
        print("Successfully patched beeline.sh with --enable-preview!")
    else:
        print("Target string not found in beeline.sh")
else:
    print("Already patched!")
