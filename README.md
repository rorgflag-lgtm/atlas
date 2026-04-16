```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       █████╗ ████████╗██╗      █████╗ ███████╗   v1.0.0      ║
║      ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝               ║
║      ███████║   ██║   ██║     ███████║███████╗               ║
║      ██╔══██║   ██║   ██║     ██╔══██║╚════██║               ║
║      ██║  ██║   ██║   ███████╗██║  ██║███████║               ║
║      ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝               ║
║                                                              ║
║              The Pillar of Artificial Intelligence           ║
║                                                              ║
║          Neurosymbolic AI Operating System                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

# ATLAS OS

**ATLAS is not a tool. It is an operating system for artificial intelligence.**

Built on a proprietary architecture — also called ATLAS — it allows anyone to create, train, fine-tune and deploy their own AI, at zero cost.

Your data never leaves your device.  
Your model weights are stored locally.  
Training and inference are free.

---

## What is ATLAS

Most AI systems today are built on Transformers, RNNs or similar architectures.  
ATLAS is none of these.

ATLAS is a new architecture, designed from the ground up with one long-term objective :  
**neurosymbolic AI, democratized for everyone.**

We are close.

The system currently allows you to :

- Create an AI from scratch or start from a pre-trained base
- Train it on any raw text corpus
- Fine-tune it on structured input/reply pairs
- Run inference directly in your terminal
- Connect it to Telegram, WhatsApp or Discord and control it remotely

Training and inference are completely free.

---

## Architecture

ATLAS does not rely on any existing architecture.  
It is a proprietary design built to eliminate the cost barrier of AI — both for training and inference.

| Property            | ATLAS                        |
|---------------------|------------------------------|
| Architecture        | Proprietary (ATLAS)          |
| Training cost       | Free                         |
| Inference cost      | Free                         |
| Your data           | Stays on your device         |
| Your model weights  | Stored locally               |
| Long-term goal      | Neurosymbolic AI for all     |

---

## Installation

**Requirements**
- Python 3.10 or higher
- Git

**1 — Clone the repository**

```bash
git clone https://github.com/your-username/atlas.git
cd atlas
```

**2 — Install dependencies**

```bash
pip install -r requirements.txt
```

**3 — Configure the API**

```bash
cp api_config.example.py api_config.py
```

Open `api_config.py` and fill in your `API_BASE_URL` and `API_KEY`.

**4 — Launch ATLAS**

```bash
python atlas.py
```

ATLAS will guide you through the setup on first launch.  
Language selection, AI naming, model type and communication channels — everything is configured interactively.

---

## Commands

| Command | Description |
|---------|-------------|
| `python atlas.py` | First launch or main menu |
| `python atlas.py init <name>` | Start your AI and chat |
| `python atlas.py /train <file.txt>` | Train your AI on a text corpus |
| `python atlas.py /finetuning <file.txt>` | Fine-tune your AI |
| `python atlas.py status` | Show your AI status and commands |
| `python atlas.py reset` | Reconfigure from scratch |

---

## Corpus Format

**Training — raw text**

```
Any continuous text is accepted.
The sky is blue. ATLAS transforms the way we build AI.
```

**Fine-tuning — structured pairs**

```
input : Hello, how are you?
reply : I am doing very well, thank you.

input : What is your purpose?
reply : I am an AI created with ATLAS.
```

---

## Communication Channels

Once your AI is configured, you can connect it to external channels and interact with it remotely.

**Supported channels**

- Telegram
- WhatsApp (via Twilio)
- Discord

**Remote commands available from any channel**

```
<message>                     →  Chat with your AI
/train <your text>            →  Train your AI remotely
/finetuning input : ...
               reply : ...    →  Fine-tune your AI remotely
```

---

## Current Limitations

These limitations are temporary and will be lifted in future releases.

| Limitation | Current value |
|------------|---------------|
| Daily usage quota | 4 hours / day |
| Max epochs per training | 200 |
| Available dimensions | 32D, 64D, 128D |

---

## Roadmap

- Additional model dimensions
- More communication channels
- Extended daily quota
- Neurosymbolic reasoning layer
- Multi-agent support

---

## License

MIT License — free to use, modify and distribute.

---

*ATLAS is an independent project. Its goal is to make artificial intelligence genuinely accessible —  
not as a service, but as a system you own and control.*