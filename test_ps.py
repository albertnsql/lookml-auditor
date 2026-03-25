import threading, queue, subprocess
import time

q = queue.Queue(maxsize=1)

def _worker():
    print("Worker started")
    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
        "$d.Description = 'Select your LookML project folder';"
        "$d.ShowNewFolderButton = $false;"
        "$f = New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
        "$r = $d.ShowDialog($f);"
        "if ($r -eq [System.Windows.Forms.DialogResult]::OK)"
        "{ Write-Output $d.SelectedPath }"
    )
    result = subprocess.run(
        ["powershell", "-STA", "-WindowStyle", "Hidden",
         "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True, text=True, timeout=120,
    )
    print("Return code:", result.returncode)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
    q.put(result.stdout.strip())

t = threading.Thread(target=_worker, daemon=True)
t.start()
time.sleep(1)
print("Finished waiting")
