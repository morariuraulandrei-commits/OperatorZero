# OperatorZero 🔐

**Bot Telegram de intelligence pentru securitate cibernetica.**
Monitorizeaza automat surse RSS, forumuri si Reddit, postând **6 stiri noi la fiecare 5 minute** in canalul tau Telegram.

---

## 📡 Surse monitorizate (18 surse)

| Sursa | Domeniu |
|---|---|
| The Hacker News | Cybersecurity general |
| Bleeping Computer | Malware, ransomware, breach |
| Krebs on Security | Investigatii securitate |
| Dark Reading | Vulnerabilitati, APT |
| SecurityWeek | Threat intelligence |
| Naked Security (Sophos) | Malware analysis |
| Malwarebytes Labs | Malware, exploituri |
| Exploit-DB | Exploituri publice |
| CISA Alerts | Alerte guvernamentale SUA |
| Graham Cluley | Cybersecurity news |
| Threatpost | Vulnerabilitati CVE |
| Reddit r/netsec | Comunitate securitate |
| Reddit r/Malware | Malware analysis |
| Reddit r/hacking | Hacking & pentesting |
| Reddit r/cybersecurity | Stiri generale |
| Packet Storm | Exploituri, tools |
| CXSecurity | Vulnerabilitati |
| Full Disclosure | Disclosure responsabil |

---

## 🚀 Instalare

```bash
git clone https://github.com/morariuraulandrei-commits/OperatorZero.git
cd OperatorZero
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
```

Editeaza `.env`:
- `CHANNEL_ID` — ID-ul canalului/grupului (ex: `@canalul_meu`)
- Adauga botul ca **Administrator** in canal cu permisiunea de a posta!

```bash
python bot.py
```

---

## 🤖 Comenzi

| Comanda | Descriere |
|---|---|
| `/start` | Info bot |
| `/status` | Stare + statistici |
| `/setchannel @id` | Seteaza canalul |
| `/fetch` | Actualizeaza manual |
| `/stats` | Statistici articole |
