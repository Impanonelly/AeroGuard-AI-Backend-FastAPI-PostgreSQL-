# 🚀 How to Restart the Server - Beginner's Guide

## 📍 Where is the Server Running?

The server is running in your **VS Code Terminal**. You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## 🛑 Step 1: Stop the Server

1. **Find the terminal window** where the server is running
   - It's the terminal in VS Code (usually at the bottom)
   - You should see the server output/logs there

2. **Click inside that terminal** (click anywhere in the terminal window)

3. **Press these keys together**: 
   - `CTRL` + `C`
   - (Hold CTRL, then press C, then release both)

4. **What you should see**:
   - The server will stop
   - You'll see something like: `KeyboardInterrupt` or the command prompt returns
   - You'll see `(venv) PS E:\...>` again (your prompt)

---

## ▶️ Step 2: Start the Server Again

After stopping, run this command in the **same terminal**:

```powershell
python -m uvicorn main:app --reload
```

**OR** if that doesn't work, try:

```powershell
C:\Python314\python.exe -m uvicorn main:app --reload
```

---

## ✅ Step 3: Verify It's Running

After running the command, you should see:

```
INFO:     Will watch for changes in these directories: ['E:\\Study material\\Sem 6\\Final Year Project\\aeroguard_backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**If you see "Application startup complete"** - the server is running! ✅

---

## 🌐 Step 4: Refresh Your Browser

1. Go to: http://localhost:8000/docs
2. Press `CTRL + F5` (hard refresh)
3. Look for the **Authorize** button at the top right

---

## 📸 Visual Guide

```
┌─────────────────────────────────────────┐
│  VS Code Terminal                       │
│                                         │
│  INFO: Uvicorn running...              │
│  INFO: Application startup complete.    │
│                                         │
│  ← Click here, then press CTRL+C        │
│                                         │
└─────────────────────────────────────────┘

After CTRL+C:
┌─────────────────────────────────────────┐
│  (venv) PS E:\...>                      │
│                                         │
│  ← Type your command here              │
│                                         │
└─────────────────────────────────────────┘
```

---

## ❓ Troubleshooting

### Problem: I don't see the terminal
**Solution**: 
- Press `CTRL + ~` (backtick) to open terminal in VS Code
- Or go to: View → Terminal

### Problem: CTRL+C doesn't work
**Solution**:
- Make sure you clicked inside the terminal first
- Try clicking in the terminal, then press CTRL+C again
- If still not working, close the terminal tab and open a new one

### Problem: Command not found after restart
**Solution**:
- Make sure you're in the project folder
- Run: `cd "E:\Study material\Sem 6\Final Year Project\aeroguard_backend"`
- Then run the uvicorn command

---

## 🎯 Quick Checklist

- [ ] Found the terminal with server running
- [ ] Clicked inside the terminal
- [ ] Pressed CTRL+C
- [ ] Server stopped (saw command prompt)
- [ ] Ran: `python -m uvicorn main:app --reload`
- [ ] Saw "Application startup complete"
- [ ] Refreshed browser (CTRL+F5)
- [ ] Checked for Authorize button

---

**Try these steps and let me know what happens!** 🚀

