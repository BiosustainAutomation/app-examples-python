# Benchling Canvas Demo for Biosustain

Welcome to the exciting world of Benchling Canvas. There is some tricks to getting setup but once you are able to connect and pull information you can execute arbitrary code on entities (including custom entities that contain files).

Step 

## Step 1:🔌 Installing ngrok

To install [ngrok](https://ngrok.com/) for local tunneling:

### Make a free ngrok account

Go to https://ngrok.com/ and setup a free account.

### Install ngrok (macOS / Linux)
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok
```

You will need your account password you got when setting up on the virtual machine.

### 🔐 Connect Your Account
After installing, run the following command with your auth token (found in your ngrok dashboard):

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

Launch ngrok with:

```bash
ngrok https PORT_NUMBER
```
