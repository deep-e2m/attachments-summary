# Docker: Complete Guide from Zero to Production

A comprehensive guide to understanding Docker deeply, written in simple language with real examples.

---

## Table of Contents

1. [Introduction - What & Why Docker](#1-introduction---what--why-docker)
2. [Core Docker Concepts](#2-core-docker-concepts)
3. [Installing Docker](#3-installing-docker)
4. [Running Your First Container](#4-running-your-first-container)
5. [Understanding Dockerfile](#5-understanding-dockerfile-deep-explanation)
6. [Python Application Example](#6-python-application-example)
7. [Building Docker Images](#7-building-docker-images)
8. [Running Containers Like a Pro](#8-running-containers-like-a-pro)
9. [Volumes & Data Persistence](#9-volumes--data-persistence)
10. [Environment Variables & Secrets](#10-environment-variables--secrets)
11. [Docker Networking](#11-docker-networking)
12. [Docker Compose](#12-docker-compose)
13. [Production Readiness](#13-production-readiness)
14. [Common Errors & Debugging](#14-common-errors--debugging)
15. [Mental Model](#15-mental-model---how-to-think-in-docker)
16. [Command Cheat Sheet](#16-command-cheat-sheet)

---

## 1. Introduction - What & Why Docker

### What is Docker? (Simple Explanation)

Docker is a tool that packages your application along with everything it needs to run (Python version, libraries, system tools) into a single unit called a **container**.

Think of it like this:

```
Without Docker:
"Hey, can you run my Python app?"
"Sure... wait, I have Python 3.8, you need 3.11"
"Also, I'm missing these 15 libraries"
"And my operating system is different"
😫 Doesn't work!

With Docker:
"Hey, here's my Docker container"
"Running it now... works perfectly!"
😊 Same result everywhere!
```

### Real-Life Analogy: Shipping Containers

Before shipping containers existed:
- Workers manually loaded different-shaped cargo onto ships
- Each port handled goods differently
- Things got damaged, lost, or delayed

After shipping containers:
- Everything goes into standard-sized boxes
- Any ship, truck, or crane can handle them
- Contents don't matter - the container is the standard

**Docker does the same for software:**

```
┌─────────────────────────────────────────────────────────┐
│                  SHIPPING CONTAINER                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Bananas │ │ TVs     │ │ Clothes │ │ Toys    │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│  Contents don't matter - container is standard          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   DOCKER CONTAINER                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Python  │ │ FastAPI │ │ Libraries│ │ Your App│       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│  Contents packaged - runs same everywhere               │
└─────────────────────────────────────────────────────────┘
```

### Problems Docker Solves

| Problem | Without Docker | With Docker |
|---------|---------------|-------------|
| "Works on my machine" | Different environments cause bugs | Same environment everywhere |
| Dependency conflicts | App A needs Python 3.8, App B needs 3.11 | Each app has its own isolated environment |
| Setup complexity | "Install these 20 things first" | `docker run` and done |
| Server differences | Dev laptop ≠ Production server | Container runs identically |
| Cleanup | Uninstalling leaves junk files | Delete container, everything gone |

### Where Can Your App Run?

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                          │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌────────────┐    ┌────────────┐    ┌────────────┐
    │  LOCALLY   │    │   DOCKER   │    │   SERVER   │
    │            │    │            │    │            │
    │ Your laptop│    │ Container  │    │ Cloud/VPS  │
    │ Direct run │    │ Isolated   │    │ Production │
    │            │    │            │    │            │
    │ python     │    │ docker run │    │ docker run │
    │ main.py    │    │ myapp      │    │ myapp      │
    └────────────┘    └────────────┘    └────────────┘

    Depends on       Same result        Same result
    your setup       everywhere         as your laptop
```

**Key insight:** Docker containers run the same way on your laptop, your colleague's laptop, and the production server.

---

## 2. Core Docker Concepts

### Image vs Container (MOST IMPORTANT CONCEPT)

This is the #1 thing beginners confuse. Let me make it crystal clear:

```
IMAGE = Recipe/Blueprint (static file, doesn't run)
CONTAINER = Running instance of that recipe (actually running)
```

**Analogy:**

```
IMAGE = Cookie cutter (the shape/template)
CONTAINER = Actual cookie (made from the cutter)

You can make MANY cookies from ONE cookie cutter.
You can run MANY containers from ONE image.
```

**Visual:**

```
┌─────────────────┐
│     IMAGE       │
│   (Blueprint)   │
│                 │
│  - Python 3.11  │
│  - FastAPI      │
│  - Your code    │
│                 │
│  Just a file,   │
│  doesn't run    │
└────────┬────────┘
         │
         │ docker run
         │
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   CONTAINER 1   │  │   CONTAINER 2   │  │   CONTAINER 3   │
│   (Running)     │  │   (Running)     │  │   (Running)     │
│                 │  │                 │  │                 │
│   Port 8000     │  │   Port 8001     │  │   Port 8002     │
│                 │  │                 │  │                 │
│   Isolated!     │  │   Isolated!     │  │   Isolated!     │
└─────────────────┘  └─────────────────┘  └─────────────────┘

One image → Many containers
```

### Dockerfile

A Dockerfile is a text file with instructions to build an image.

```dockerfile
# This is a Dockerfile
FROM python:3.11          # Start with Python
COPY . /app               # Copy your code
RUN pip install -r requirements.txt  # Install dependencies
CMD ["python", "main.py"] # Run your app
```

**Think of it as:** A recipe that Docker follows step-by-step to create an image.

### Docker Engine

The software that runs on your machine and does all the work:
- Builds images
- Runs containers
- Manages networks
- Handles storage

```
┌─────────────────────────────────────────┐
│            YOUR COMPUTER                │
│                                         │
│   ┌─────────────────────────────────┐  │
│   │        DOCKER ENGINE            │  │
│   │                                 │  │
│   │  ┌───────┐ ┌───────┐ ┌───────┐ │  │
│   │  │ Cont. │ │ Cont. │ │ Cont. │ │  │
│   │  │   1   │ │   2   │ │   3   │ │  │
│   │  └───────┘ └───────┘ └───────┘ │  │
│   │                                 │  │
│   └─────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

### Docker CLI

The command-line tool you use to talk to Docker Engine:

```bash
docker build    # Create an image
docker run      # Start a container
docker ps       # List running containers
docker stop     # Stop a container
docker images   # List images
```

### Docker Registry (Docker Hub)

A place to store and share Docker images. Like GitHub for code, but for Docker images.

```
┌──────────────────┐         ┌──────────────────┐
│   YOUR LAPTOP    │         │   DOCKER HUB     │
│                  │  push   │                  │
│   myapp:v1.0     │ ──────► │   myapp:v1.0     │
│                  │         │                  │
│                  │  pull   │                  │
│   python:3.11    │ ◄────── │   python:3.11    │
│                  │         │                  │
└──────────────────┘         └──────────────────┘
```

**Common registries:**
- Docker Hub (public, default)
- Amazon ECR
- Google Container Registry
- GitHub Container Registry

### Layers (How Docker Caches)

Each instruction in a Dockerfile creates a **layer**. Docker caches these layers to speed up builds.

```dockerfile
FROM python:3.11              # Layer 1 (cached after first build)
WORKDIR /app                  # Layer 2 (cached)
COPY requirements.txt .       # Layer 3 (cached if file unchanged)
RUN pip install -r requirements.txt  # Layer 4 (cached if requirements unchanged)
COPY . .                      # Layer 5 (changes when code changes)
CMD ["python", "main.py"]     # Layer 6
```

**Visual:**

```
┌─────────────────────────────────────┐
│  Layer 6: CMD                       │  ← Top (your command)
├─────────────────────────────────────┤
│  Layer 5: COPY . .                  │  ← Your code (changes often)
├─────────────────────────────────────┤
│  Layer 4: pip install               │  ← Dependencies (cached!)
├─────────────────────────────────────┤
│  Layer 3: COPY requirements.txt     │  ← (cached!)
├─────────────────────────────────────┤
│  Layer 2: WORKDIR /app              │  ← (cached!)
├─────────────────────────────────────┤
│  Layer 1: python:3.11               │  ← Base image (cached!)
└─────────────────────────────────────┘

When you change code, only Layer 5 and above rebuild!
Layers 1-4 are cached = FAST builds!
```

**Common Beginner Mistake:**

```dockerfile
# BAD - Slow builds ❌
COPY . .                              # Code changes = invalidates cache
RUN pip install -r requirements.txt   # Reinstalls EVERY time!

# GOOD - Fast builds ✅
COPY requirements.txt .               # Only this file
RUN pip install -r requirements.txt   # Cached if requirements unchanged
COPY . .                              # Code changes don't affect pip install
```

---

## 3. Installing Docker

### Docker Desktop vs Docker Engine

| Feature | Docker Desktop | Docker Engine |
|---------|---------------|---------------|
| GUI | Yes | No (CLI only) |
| Platform | Mac, Windows, Linux | Linux only |
| Ease | Beginner-friendly | Advanced |
| Resources | Uses more RAM | Lightweight |
| Free for | Personal use | Everyone |

**Recommendation:** Use Docker Desktop if you're on Mac or Windows.

### Installation Steps

**Mac:**
1. Go to https://www.docker.com/products/docker-desktop
2. Download Docker Desktop for Mac
3. Double-click the `.dmg` file
4. Drag Docker to Applications
5. Open Docker from Applications
6. Wait for it to start (whale icon in menu bar)

**Windows:**
1. Go to https://www.docker.com/products/docker-desktop
2. Download Docker Desktop for Windows
3. Run the installer
4. Enable WSL 2 when prompted
5. Restart your computer
6. Open Docker Desktop

**Linux (Ubuntu):**
```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Log out and log back in, then test
docker run hello-world
```

### Verify Installation

```bash
# Check Docker version
docker --version
# Output: Docker version 24.0.5, build 24.0.5-0ubuntu1

# Check detailed info
docker info
# Shows: containers, images, server version, etc.

# List running containers (should be empty)
docker ps
# Output: CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES

# Test with hello-world
docker run hello-world
# Should download and run a test container
```

**If you see errors:**
- Make sure Docker Desktop is running (check for whale icon)
- On Linux, make sure you added your user to the docker group
- Try `sudo docker ps` to test if it's a permissions issue

---

## 4. Running Your First Container

### The `docker run` Command

This is the most important command. Let's break it down:

```bash
docker run [OPTIONS] IMAGE [COMMAND]
```

**What happens when you run `docker run`:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker run python:3.11                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Is image "python:3.11" on my computer?                  │
│         NO → Download from Docker Hub                           │
│         YES → Use local image                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Create a new container from the image                   │
│         (Like making a cookie from the cutter)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Start the container                                     │
│         (Container is now running!)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Run the default command (or your custom command)        │
│         (For python:3.11, it opens Python shell)                │
└─────────────────────────────────────────────────────────────────┘
```

### Important Flags

#### `-it` (Interactive + TTY)

```bash
# Without -it: Container runs and exits immediately
docker run python:3.11
# Nothing happens, exits immediately

# With -it: You get an interactive shell
docker run -it python:3.11
# Python 3.11.0 (main, Oct 24 2022, 18:26:48)
# >>> print("Hello!")
# Hello!
# >>> exit()
```

**What do -i and -t mean?**
- `-i` = Interactive (keep STDIN open, so you can type)
- `-t` = TTY (allocate a terminal, so output looks nice)
- `-it` = Both together (most common usage)

#### `-d` (Detached Mode)

```bash
# Without -d: Container runs in foreground (blocks your terminal)
docker run nginx
# Terminal is stuck showing nginx logs...

# With -d: Container runs in background
docker run -d nginx
# a1b2c3d4e5f6...  (returns container ID, terminal is free)

# Check it's running
docker ps
# Shows nginx container running
```

#### `-p` (Port Mapping) - VERY IMPORTANT

Containers are isolated. To access a service inside, you must map ports.

```bash
docker run -d -p 8080:80 nginx
#              ────┬────
#                  │
#     ┌────────────┴────────────┐
#     │                         │
#  HOST:8080              CONTAINER:80
#  (your computer)        (inside container)
```

**Visual:**

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR COMPUTER                            │
│                                                              │
│   Browser → http://localhost:8080                           │
│                      │                                       │
│                      ▼                                       │
│              ┌───────────────┐                              │
│              │   Port 8080   │  ← Host port                 │
│              └───────┬───────┘                              │
│                      │ mapped to                             │
│              ┌───────▼───────┐                              │
│              │   Port 80     │  ← Container port            │
│              │   ┌───────┐   │                              │
│              │   │ NGINX │   │                              │
│              │   └───────┘   │                              │
│              │  CONTAINER    │                              │
│              └───────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

**Common port mappings:**

```bash
# Same port on both sides
docker run -p 8000:8000 myapp

# Different ports
docker run -p 3000:8000 myapp
# Access via localhost:3000, app runs on 8000 inside

# Multiple ports
docker run -p 8000:8000 -p 5432:5432 myapp
```

#### `--name` (Give Container a Name)

```bash
# Without name: Docker assigns random name
docker run -d nginx
docker ps
# NAMES: determined_hopper (random!)

# With name: You choose the name
docker run -d --name my-nginx nginx
docker ps
# NAMES: my-nginx

# Now you can use the name
docker stop my-nginx
docker start my-nginx
docker logs my-nginx
```

#### `--rm` (Auto-Remove When Stopped)

```bash
# Without --rm: Container stays after stopping
docker run -d --name test nginx
docker stop test
docker ps -a  # Shows stopped container (still exists!)

# With --rm: Container is deleted when stopped
docker run -d --rm --name test nginx
docker stop test
docker ps -a  # Container is gone!
```

**Use `--rm` for:** Testing, temporary containers, one-time tasks

### Example 1: Run Python Container

```bash
# Interactive Python shell
docker run -it python:3.11

# You're now inside Python
>>> print("Hello from Docker!")
Hello from Docker!
>>> import sys
>>> sys.version
'3.11.0 (main, Oct 24 2022, 18:26:48) [GCC 10.2.1 20210110]'
>>> exit()

# Run a Python command directly
docker run python:3.11 python -c "print('Hello!')"
# Output: Hello!
```

### Example 2: Run Nginx Container

```bash
# Run Nginx web server
docker run -d -p 8080:80 --name webserver nginx

# Check it's running
docker ps
# CONTAINER ID   IMAGE   PORTS                  NAMES
# a1b2c3d4e5f6   nginx   0.0.0.0:8080->80/tcp   webserver

# Open browser: http://localhost:8080
# You'll see "Welcome to nginx!" page

# View logs
docker logs webserver

# Stop it
docker stop webserver

# Remove it
docker rm webserver
```

### Port Mapping Explained Clearly

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  docker run -p 3000:8000 myapp                                │
│                 │    │                                         │
│                 │    └── Container port (app listens here)     │
│                 │                                              │
│                 └─────── Host port (you access this)           │
│                                                                │
│  Browser: http://localhost:3000  ──────►  App on port 8000    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Remember:** `HOST:CONTAINER` - Left side is YOUR computer, right side is INSIDE the container.

---

## 5. Understanding Dockerfile (DEEP EXPLANATION)

A Dockerfile is a text file that contains instructions to build a Docker image. Let's understand each instruction deeply.

### FROM

**What it does:** Sets the base image (starting point)

**Why it's used:** Every Docker image needs a foundation. You build ON TOP of an existing image.

```dockerfile
# Use official Python image
FROM python:3.11

# Use slim version (smaller)
FROM python:3.11-slim

# Use Alpine (very small, but may have compatibility issues)
FROM python:3.11-alpine

# Use Ubuntu as base
FROM ubuntu:22.04
```

**Visual:**

```
┌─────────────────────────────────┐
│  Your App Layer                 │  ← What you add
├─────────────────────────────────┤
│  pip packages                   │  ← What you add
├─────────────────────────────────┤
│  Python 3.11                    │  ← FROM python:3.11
├─────────────────────────────────┤
│  Debian Linux                   │  ← Included in python image
└─────────────────────────────────┘
```

**Common Mistake:**
```dockerfile
# Wrong: Using "latest" tag
FROM python:latest  # ❌ Version can change unexpectedly!

# Right: Pin the version
FROM python:3.11    # ✅ Always the same version
```

### WORKDIR

**What it does:** Sets the working directory inside the container

**Why it's used:** All following commands run from this directory

```dockerfile
WORKDIR /app

# Now these commands run inside /app:
COPY . .          # Copies to /app
RUN pip install   # Runs in /app
CMD ["python", "main.py"]  # Runs from /app
```

**Visual:**

```
Container filesystem:
/
├── bin/
├── etc/
├── home/
├── app/          ← WORKDIR /app (you are here)
│   ├── main.py
│   ├── requirements.txt
│   └── ...
└── ...
```

**Without WORKDIR:**
```dockerfile
# Messy! Files go to root directory
COPY . /app
RUN cd /app && pip install -r requirements.txt
CMD ["python", "/app/main.py"]
```

**With WORKDIR:**
```dockerfile
# Clean! Everything relative to /app
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### COPY

**What it does:** Copies files from your computer into the image

**Syntax:** `COPY <source> <destination>`

```dockerfile
WORKDIR /app

# Copy single file
COPY requirements.txt .

# Copy everything
COPY . .

# Copy specific folder
COPY src/ ./src/

# Copy multiple files
COPY package.json package-lock.json ./
```

**What `.` means:**

```dockerfile
COPY requirements.txt .
#                     │
#                     └── Current directory IN CONTAINER
#                         (which is /app because of WORKDIR)

# Same as:
COPY requirements.txt /app/requirements.txt
```

**Common Mistake:**
```dockerfile
# Copying unnecessary files
COPY . .  # Copies EVERYTHING including node_modules, .git, etc.

# Solution: Use .dockerignore file
```

**.dockerignore file (create this!):**
```
.git
.gitignore
__pycache__
*.pyc
.env
venv/
node_modules/
.DS_Store
*.log
```

### RUN

**What it does:** Executes a command during IMAGE BUILD

**Why it's used:** Install packages, create directories, download files

```dockerfile
# Install Python packages
RUN pip install -r requirements.txt

# Install system packages
RUN apt-get update && apt-get install -y curl

# Create directory
RUN mkdir -p /app/logs

# Multiple commands (combine for fewer layers)
RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*
```

**RUN vs CMD:**
```
RUN  = Runs during BUILD (creates layers in image)
CMD  = Runs when CONTAINER STARTS (not during build)
```

**Common Mistake:**
```dockerfile
# Bad: Many RUN commands = many layers = larger image
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*

# Good: Single RUN command = one layer
RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*
```

### CMD

**What it does:** Sets the DEFAULT command to run when container starts

**Important:** Only ONE CMD is used (last one wins)

```dockerfile
# Exec form (RECOMMENDED)
CMD ["python", "main.py"]

# Shell form
CMD python main.py
```

**Exec form vs Shell form:**
```dockerfile
# Exec form: ["executable", "param1", "param2"]
CMD ["python", "main.py"]
# - Runs directly, no shell
# - Signals handled properly
# - RECOMMENDED

# Shell form: command param1 param2
CMD python main.py
# - Runs via /bin/sh -c
# - Shell features available (pipes, variables)
# - Signals may not work properly
```

**CMD can be overridden:**
```bash
# Dockerfile has: CMD ["python", "main.py"]

# Run with default command
docker run myapp
# Runs: python main.py

# Override the command
docker run myapp python other_script.py
# Runs: python other_script.py (CMD ignored!)
```

### ENTRYPOINT

**What it does:** Sets the main executable (harder to override than CMD)

**ENTRYPOINT vs CMD:**

```dockerfile
# CMD only: Easy to override
CMD ["python", "main.py"]
# docker run myapp            → python main.py
# docker run myapp bash       → bash (CMD replaced!)

# ENTRYPOINT only: Always runs python
ENTRYPOINT ["python"]
# docker run myapp            → python
# docker run myapp main.py    → python main.py

# ENTRYPOINT + CMD: Best of both
ENTRYPOINT ["python"]
CMD ["main.py"]
# docker run myapp            → python main.py
# docker run myapp other.py   → python other.py (only CMD replaced)
```

**Use Case:**

```dockerfile
# Always run as Python script executor
ENTRYPOINT ["python"]
CMD ["main.py"]

# Users can:
# docker run myapp           → python main.py
# docker run myapp test.py   → python test.py
# docker run myapp -c "print('hi')"  → python -c "print('hi')"
```

### EXPOSE

**What it does:** Documents which port the app uses (DOES NOT PUBLISH IT!)

```dockerfile
EXPOSE 8000
```

**Important:** EXPOSE is just documentation! It doesn't actually open the port.

```bash
# EXPOSE alone does nothing for access
docker run myapp
# Cannot access port 8000 from outside!

# You still need -p to publish
docker run -p 8000:8000 myapp
# Now you can access port 8000
```

**Why use EXPOSE?**
- Documentation for others
- Works with `docker run -P` (auto-map exposed ports)
- Shows in `docker ps` output

### ENV

**What it does:** Sets environment variables

```dockerfile
# Single variable
ENV APP_ENV=production

# Multiple variables
ENV APP_ENV=production \
    APP_PORT=8000 \
    DEBUG=false

# Use the variable
ENV APP_HOME=/app
WORKDIR $APP_HOME
```

**ENV vs ARG:**
```dockerfile
# ARG: Only available during BUILD
ARG VERSION=1.0
RUN echo "Building version $VERSION"

# ENV: Available during BUILD and RUNTIME
ENV APP_VERSION=1.0
# Can be accessed by your running app
```

---

## 6. Python Application Example

Let's build a Docker image for a real Python application.

### Project Structure

```
myapp/
├── main.py
├── requirements.txt
└── Dockerfile
```

**main.py:**
```python
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Docker!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn==0.24.0
```

**Dockerfile:**
```dockerfile
# Step 1: Start with Python base image
FROM python:3.11-slim

# Step 2: Set working directory
WORKDIR /app

# Step 3: Copy requirements first (for caching)
COPY requirements.txt .

# Step 4: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy application code
COPY . .

# Step 6: Document the port
EXPOSE 8000

# Step 7: Run the application
CMD ["python", "main.py"]
```

### Why This Order? (Layer Caching Explained)

```
┌─────────────────────────────────────────────────────────────────┐
│  Dockerfile Instruction        │  When does this layer rebuild? │
├─────────────────────────────────────────────────────────────────┤
│  FROM python:3.11-slim         │  Never (base image)            │
│  WORKDIR /app                  │  Never (static)                │
│  COPY requirements.txt .       │  Only if requirements change   │
│  RUN pip install ...           │  Only if requirements change   │
│  COPY . .                      │  Every time code changes       │
│  CMD ["python", "main.py"]     │  Never (static)                │
└─────────────────────────────────────────────────────────────────┘

Your code changes often, but requirements rarely change.
By copying requirements FIRST, pip install is CACHED!
```

**Bad order (slow builds):**
```dockerfile
COPY . .                              # Code change = cache invalidated HERE
RUN pip install -r requirements.txt   # Runs EVERY time (slow!)
```

**Good order (fast builds):**
```dockerfile
COPY requirements.txt .               # Only requirements file
RUN pip install -r requirements.txt   # Cached if requirements unchanged!
COPY . .                              # Code changes don't affect pip install
```

### Building the Image Step-by-Step

```bash
# Navigate to your project
cd myapp/

# Build the image
docker build -t myapp:1.0 .
```

**What happens during build:**

```
$ docker build -t myapp:1.0 .

Step 1/7 : FROM python:3.11-slim
 ---> a1b2c3d4e5f6

Step 2/7 : WORKDIR /app
 ---> Running in xyz123
 ---> b2c3d4e5f6a7

Step 3/7 : COPY requirements.txt .
 ---> c3d4e5f6a7b8

Step 4/7 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Running in abc456
Collecting fastapi==0.104.1
Collecting uvicorn==0.24.0
Installing collected packages: ...
 ---> d4e5f6a7b8c9

Step 5/7 : COPY . .
 ---> e5f6a7b8c9d0

Step 6/7 : EXPOSE 8000
 ---> f6a7b8c9d0e1

Step 7/7 : CMD ["python", "main.py"]
 ---> g7b8c9d0e1f2

Successfully built g7b8c9d0e1f2
Successfully tagged myapp:1.0
```

### Running the Container

```bash
# Run the container
docker run -d -p 8000:8000 --name myapp myapp:1.0

# Check it's running
docker ps
# CONTAINER ID   IMAGE       PORTS                    NAMES
# abc123         myapp:1.0   0.0.0.0:8000->8000/tcp   myapp

# Test the app
curl http://localhost:8000
# {"message":"Hello from Docker!"}

curl http://localhost:8000/health
# {"status":"healthy"}

# View logs
docker logs myapp

# Stop and remove
docker stop myapp
docker rm myapp
```

---

## 7. Building Docker Images

### The `docker build` Command

```bash
docker build [OPTIONS] PATH

# Common usage
docker build -t myapp:1.0 .
#            │  │      │  │
#            │  │      │  └── Build context (current directory)
#            │  │      └───── Tag version
#            │  └──────────── Image name
#            └─────────────── Tag flag
```

### Tags and Naming

**Image naming convention:**
```
[registry/][username/]repository[:tag]

Examples:
myapp                          # Local image, latest tag (implicit)
myapp:1.0                      # Local image, version 1.0
myapp:latest                   # Local image, latest tag (explicit)
deeptrivedi/myapp:1.0          # Docker Hub image
gcr.io/myproject/myapp:1.0     # Google Container Registry
```

**Tagging examples:**
```bash
# Build with tag
docker build -t myapp:1.0 .

# Add another tag to existing image
docker tag myapp:1.0 myapp:latest

# Tag for Docker Hub
docker tag myapp:1.0 deeptrivedi/myapp:1.0

# Build with multiple tags
docker build -t myapp:1.0 -t myapp:latest .
```

### Viewing Images

```bash
# List all images
docker images
# REPOSITORY   TAG       IMAGE ID       CREATED          SIZE
# myapp        1.0       a1b2c3d4e5f6   5 minutes ago    150MB
# python       3.11      b2c3d4e5f6a7   2 weeks ago      1.01GB

# Filter images
docker images myapp
# Shows only myapp images

# Show image history (layers)
docker history myapp:1.0
# Shows each layer and its size
```

### Understanding Build Context

The `.` at the end of `docker build -t myapp .` is the **build context**.

```bash
docker build -t myapp .
#                     └── This directory is sent to Docker daemon
```

**Everything in this directory is sent to Docker!**

```
myapp/
├── main.py           # ✅ Sent (needed)
├── requirements.txt  # ✅ Sent (needed)
├── Dockerfile        # ✅ Sent (needed)
├── .git/             # ❌ Sent (NOT needed! Wastes time)
├── venv/             # ❌ Sent (NOT needed! Huge!)
├── __pycache__/      # ❌ Sent (NOT needed!)
└── node_modules/     # ❌ Sent (NOT needed! Huge!)
```

**Always create `.dockerignore`:**
```
.git
.gitignore
__pycache__
*.pyc
.env
venv/
.venv/
node_modules/
*.log
.DS_Store
Dockerfile
docker-compose.yml
README.md
```

### What Happens During Build

```
┌──────────────────────────────────────────────────────────────────┐
│                    docker build -t myapp .                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. Docker CLI sends build context to Docker daemon               │
│    (All files in current directory, except .dockerignore)        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. Docker reads Dockerfile                                       │
│    Parses each instruction                                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. For each instruction:                                         │
│    - Check if layer exists in cache                              │
│    - If cached: Use existing layer (fast!)                       │
│    - If not cached: Execute instruction, create new layer        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Stack all layers together = Final image                       │
│    Tag it with the name you specified                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Running Containers Like a Pro

### Container Lifecycle

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Created │ ──► │ Running │ ──► │ Stopped │ ──► │ Removed │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │
 docker run     docker stop     docker start    docker rm
 docker create  docker kill     docker restart
```

### `docker run` vs `docker start`

```bash
# docker run = CREATE + START (new container)
docker run -d --name web nginx
# Creates a NEW container and starts it

# docker start = START existing container
docker stop web
docker start web
# Starts the SAME container (keeps data, config)
```

### `docker stop` vs `docker kill`

```bash
# docker stop = Graceful shutdown (SIGTERM)
docker stop web
# Sends SIGTERM, waits 10 seconds, then SIGKILL
# App can clean up, save state, close connections

# docker kill = Immediate shutdown (SIGKILL)
docker kill web
# Sends SIGKILL immediately
# No cleanup, just dies
```

**Use `stop` normally, `kill` only if container is stuck.**

### Viewing Logs

```bash
# View all logs
docker logs myapp

# Follow logs (like tail -f)
docker logs -f myapp

# Show last 100 lines
docker logs --tail 100 myapp

# Show logs with timestamps
docker logs -t myapp

# Show logs since specific time
docker logs --since 2023-01-01 myapp
docker logs --since 10m myapp  # Last 10 minutes
```

### Executing Commands Inside Container

```bash
# Run a command in running container
docker exec myapp ls /app
# Shows files in /app

# Interactive shell
docker exec -it myapp bash
# Now you're INSIDE the container
# root@abc123:/app# ls
# main.py  requirements.txt
# root@abc123:/app# exit

# If bash isn't available (Alpine), use sh
docker exec -it myapp sh

# Run Python inside
docker exec -it myapp python
# >>> print("Hello from inside!")
```

### Debugging Examples

**Problem: Container exits immediately**
```bash
# Check exit code and logs
docker ps -a
# STATUS: Exited (1) 5 seconds ago

docker logs myapp
# Shows error message

# Run interactively to see what happens
docker run -it myapp
```

**Problem: App not accessible**
```bash
# Check if container is running
docker ps

# Check port mapping
docker port myapp
# 8000/tcp -> 0.0.0.0:8000

# Check if app is listening inside
docker exec myapp netstat -tlnp
# or
docker exec myapp ss -tlnp

# Check logs for errors
docker logs myapp
```

**Problem: Need to check files inside**
```bash
# Get shell access
docker exec -it myapp bash

# Check files
ls -la /app
cat /app/config.py

# Check environment
env | grep APP

# Check running processes
ps aux
```

---

## 9. Volumes & Data Persistence

### Why Containers Lose Data

Containers are **ephemeral** (temporary). When you delete a container, everything inside is gone.

```
┌─────────────────────────────────────────┐
│           CONTAINER                     │
│                                         │
│   ┌─────────────┐                      │
│   │ Your data   │  ← This is INSIDE    │
│   │ logs, db    │    the container     │
│   └─────────────┘                      │
│                                         │
└─────────────────────────────────────────┘
            │
            │ docker rm myapp
            │
            ▼
        💨 GONE! All data lost!
```

### Volumes to the Rescue

Volumes store data OUTSIDE the container, on your host machine.

```
┌─────────────────────────────────────────┐
│           CONTAINER                     │
│                                         │
│   ┌─────────────┐                      │
│   │ /app/data   │ ◄───┐                │
│   └─────────────┘     │                │
│                       │ MOUNTED        │
└───────────────────────│─────────────────┘
                        │
┌───────────────────────│─────────────────┐
│           HOST        │                 │
│   ┌─────────────┐     │                │
│   │ /data       │ ◄───┘                │
│   │ (persists!) │                      │
│   └─────────────┘                      │
└─────────────────────────────────────────┘

Container deleted? Data still on host!
```

### Types of Volumes

**1. Named Volumes (Docker-managed)**
```bash
# Create a volume
docker volume create mydata

# Use it
docker run -v mydata:/app/data myapp
#            │       │
#            │       └── Path inside container
#            └────────── Volume name

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata
```

**2. Bind Mounts (You specify the path)**
```bash
# Mount current directory
docker run -v $(pwd):/app myapp

# Mount specific directory
docker run -v /home/user/data:/app/data myapp

# Read-only mount
docker run -v /home/user/config:/app/config:ro myapp
```

### When to Use Which

| Use Case | Type | Example |
|----------|------|---------|
| Database storage | Named Volume | `-v postgres_data:/var/lib/postgresql/data` |
| Log persistence | Named Volume | `-v app_logs:/app/logs` |
| Development (live code reload) | Bind Mount | `-v $(pwd):/app` |
| Config files | Bind Mount | `-v ./config.yml:/app/config.yml:ro` |

### Example: Persist Logs

```bash
# Without volume (logs lost when container deleted)
docker run -d --name app myapp
docker rm app  # Logs gone!

# With volume (logs persist)
docker run -d --name app -v app_logs:/app/logs myapp
docker rm app
docker run -d --name app -v app_logs:/app/logs myapp
# Logs still there!
```

### Example: Database Persistence

```bash
# PostgreSQL with persistent data
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=secret \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

# Delete and recreate - data survives!
docker rm -f postgres
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=secret \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
# All your databases are still there!
```

### Example: Development with Live Reload

```bash
# Mount your code directory
docker run -d \
  -p 8000:8000 \
  -v $(pwd):/app \
  --name dev \
  myapp

# Edit main.py on your host
# Changes reflect immediately in container!
# (if using a tool like uvicorn --reload)
```

---

## 10. Environment Variables & Secrets

### Setting Environment Variables

**Method 1: In Dockerfile (baked into image)**
```dockerfile
ENV APP_ENV=production
ENV DATABASE_URL=postgres://localhost/db
```

**Method 2: At runtime (more flexible)**
```bash
# Single variable
docker run -e APP_ENV=production myapp

# Multiple variables
docker run -e APP_ENV=production -e DEBUG=false myapp

# From host environment
export MY_SECRET=abc123
docker run -e MY_SECRET myapp
# Passes MY_SECRET from host to container
```

**Method 3: Using .env file**
```bash
# .env file
APP_ENV=production
DATABASE_URL=postgres://localhost/db
SECRET_KEY=supersecret123

# Use the file
docker run --env-file .env myapp
```

### Accessing Environment Variables in Your App

**Python:**
```python
import os

app_env = os.getenv("APP_ENV", "development")
database_url = os.environ["DATABASE_URL"]  # Raises error if not set
debug = os.getenv("DEBUG", "false").lower() == "true"
```

### What NOT to Store in Images

**Never put in Dockerfile:**
```dockerfile
# WRONG! ❌
ENV DATABASE_PASSWORD=supersecret123
ENV API_KEY=sk-abc123xyz
```

**Why?** Anyone who gets your image can see these:
```bash
docker history myapp
# Shows all ENV values!

docker inspect myapp
# Shows all ENV values!
```

**Instead, pass at runtime:**
```bash
# RIGHT! ✅
docker run -e DATABASE_PASSWORD=supersecret123 myapp

# Or use .env file (don't commit to git!)
docker run --env-file .env myapp
```

### Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT VARIABLES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OK in Dockerfile:              NOT OK in Dockerfile:           │
│  ✅ APP_ENV=production          ❌ DATABASE_PASSWORD=secret     │
│  ✅ PORT=8000                   ❌ API_KEY=sk-12345             │
│  ✅ PYTHONUNBUFFERED=1          ❌ AWS_SECRET_KEY=...           │
│  ✅ TZ=UTC                      ❌ JWT_SECRET=...               │
│                                                                 │
│  Rule: If it's secret, pass it at runtime, not in Dockerfile   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Docker Networking

### The localhost Confusion

This is a common source of bugs!

**On your host machine:**
- `localhost` = your computer
- `127.0.0.1` = your computer

**Inside a container:**
- `localhost` = the container itself (NOT your computer!)
- `127.0.0.1` = the container itself

```
┌──────────────────────────────────────────────────────────────────┐
│                        HOST MACHINE                              │
│  localhost = 127.0.0.1 = your computer                          │
│                                                                  │
│  ┌────────────────────┐    ┌────────────────────┐               │
│  │    CONTAINER A     │    │    CONTAINER B     │               │
│  │                    │    │                    │               │
│  │ localhost = itself │    │ localhost = itself │               │
│  │ NOT the host!      │    │ NOT the host!      │               │
│  │                    │    │ Can't reach A via  │               │
│  │                    │    │ localhost!         │               │
│  └────────────────────┘    └────────────────────┘               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Container-to-Container Communication

**Problem:** Your Python app needs to connect to a PostgreSQL container.

```bash
# This WON'T work:
docker run -d --name db postgres:15
docker run -d --name app -e DATABASE_URL=postgres://localhost:5432/db myapp
# App can't find database! localhost = app container, not db container
```

**Solution: Use Docker networks**

```bash
# Create a network
docker network create mynetwork

# Run containers on the same network
docker run -d --name db --network mynetwork postgres:15
docker run -d --name app --network mynetwork -e DATABASE_URL=postgres://db:5432/mydb myapp
#                                                                      ^^
#                                                          Container name as hostname!
```

**Visual:**

```
┌──────────────────────────────────────────────────────────────────┐
│                       mynetwork                                  │
│                                                                  │
│  ┌────────────────────┐    ┌────────────────────┐               │
│  │    db              │    │    app             │               │
│  │    (PostgreSQL)    │◄───│    (Python)        │               │
│  │                    │    │                    │               │
│  │  Hostname: "db"    │    │ Connect to "db"    │               │
│  └────────────────────┘    └────────────────────┘               │
│                                                                  │
│  Containers on same network can reach each other by NAME        │
└──────────────────────────────────────────────────────────────────┘
```

### Network Commands

```bash
# List networks
docker network ls

# Create network
docker network create mynetwork

# Inspect network (see connected containers)
docker network inspect mynetwork

# Connect existing container to network
docker network connect mynetwork mycontainer

# Disconnect from network
docker network disconnect mynetwork mycontainer

# Remove network
docker network rm mynetwork
```

### Accessing Host from Container

Sometimes your container needs to access something on your host machine.

**Mac/Windows (Docker Desktop):**
```bash
# Use special hostname
docker run myapp
# Inside container, connect to: host.docker.internal
# Example: DATABASE_URL=postgres://host.docker.internal:5432/db
```

**Linux:**
```bash
# Use host network mode (container shares host's network)
docker run --network host myapp
# Now localhost in container = host's localhost
```

---

## 12. Docker Compose

### Why Compose Exists

Running multiple containers with `docker run` is tedious:

```bash
# Without Compose (painful!)
docker network create myapp
docker run -d --name db --network myapp -e POSTGRES_PASSWORD=secret postgres:15
docker run -d --name redis --network myapp redis:7
docker run -d --name app --network myapp -p 8000:8000 -e DATABASE_URL=postgres://db/app myapp:1.0
```

With Compose, define everything in one file and run with one command.

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

volumes:
  postgres_data:
```

### Compose Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (careful!)
docker-compose down -v

# View logs
docker-compose logs
docker-compose logs app  # Specific service

# Rebuild images
docker-compose build
docker-compose up --build

# List running services
docker-compose ps

# Execute command in service
docker-compose exec app bash
```

### Full Example: Python App + PostgreSQL + Redis

**Project structure:**
```
myproject/
├── app/
│   ├── main.py
│   └── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 8000
CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:secret@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

**Run everything:**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View app logs
docker-compose logs -f app

# Stop everything
docker-compose down
```

---

## 13. Production Readiness

### Image Size Optimization

Smaller images = Faster deploys + Less storage costs

**Use slim/alpine base images:**
```dockerfile
# Full image: ~1GB
FROM python:3.11

# Slim image: ~150MB
FROM python:3.11-slim

# Alpine image: ~50MB (but may have compatibility issues)
FROM python:3.11-alpine
```

**Don't install unnecessary packages:**
```dockerfile
# Bad
RUN pip install -r requirements.txt

# Good (no cache = smaller image)
RUN pip install --no-cache-dir -r requirements.txt
```

**Clean up in the same layer:**
```dockerfile
# Bad (cleanup in separate layer doesn't reduce size)
RUN apt-get update && apt-get install -y build-essential
RUN rm -rf /var/lib/apt/lists/*

# Good (cleanup in same layer reduces size)
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*
```

### Multi-Stage Builds

Build in one stage, copy only what you need to the final image.

```dockerfile
# Stage 1: Build
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Production (slim image)
FROM python:3.11-slim
WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
CMD ["python", "main.py"]
```

**Result:**
- Builder stage has all build tools (big)
- Final image only has runtime dependencies (small)

### Security: Non-Root User

By default, containers run as root (dangerous!).

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Create non-root user
RUN useradd --create-home appuser

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
```

### Health Checks

Let Docker know if your app is healthy:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

**Check health status:**
```bash
docker ps
# STATUS: Up 5 minutes (healthy)
```

### Production Dockerfile Example

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production image
FROM python:3.11-slim

# Security: Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Document port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application
CMD ["python", "main.py"]
```

---

## 14. Common Errors & Debugging

### Error: Port Already in Use

```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Reason:** Another container or process is using port 8000

**Fix:**
```bash
# Find what's using the port
lsof -i :8000
# or
docker ps  # Check if another container uses this port

# Option 1: Stop the other container
docker stop other_container

# Option 2: Use a different port
docker run -p 8001:8000 myapp
```

### Error: Module Not Found

```
ModuleNotFoundError: No module named 'fastapi'
```

**Reason:** Dependencies not installed in image

**Fix:**
```dockerfile
# Make sure requirements.txt is copied and installed
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

**Check:**
```bash
# Verify requirements.txt exists and has the module
cat requirements.txt

# Rebuild the image
docker build --no-cache -t myapp .
```

### Error: Container Exits Immediately

```bash
docker run -d myapp
docker ps  # Container not listed!
docker ps -a  # Shows: Exited (1) 2 seconds ago
```

**Reason:** App crashed or no foreground process

**Debug:**
```bash
# Check logs
docker logs myapp

# Run interactively to see error
docker run -it myapp

# Common causes:
# 1. Python syntax error
# 2. Missing environment variable
# 3. Can't connect to database
# 4. Wrong CMD command
```

**Fix for "no foreground process":**
```dockerfile
# Wrong: Script runs and exits
CMD ["python", "setup.py"]

# Right: Long-running process
CMD ["python", "main.py"]  # main.py should have a server loop
```

### Error: COPY Failed - File Not Found

```
COPY failed: file not found in build context
```

**Reason:** File doesn't exist or is in .dockerignore

**Fix:**
```bash
# Check file exists
ls -la requirements.txt

# Check .dockerignore isn't excluding it
cat .dockerignore

# Make sure you're in the right directory
pwd
docker build -t myapp .  # The . means current directory
```

### Error: Build Cache Confusion

**Symptom:** Code changed but container runs old code

**Reason:** Docker is using cached layers

**Fix:**
```bash
# Force rebuild without cache
docker build --no-cache -t myapp .

# Or just rebuild from the changed layer
# (Make sure COPY . . comes after pip install)
```

### Error: Cannot Connect to Database

```
connection refused / could not connect to server
```

**Reason:** Database not reachable from container

**Debug:**
```bash
# Check if database container is running
docker ps | grep postgres

# Check network
docker network ls
docker network inspect mynetwork

# Check if containers are on same network
docker inspect app --format='{{.NetworkSettings.Networks}}'
docker inspect db --format='{{.NetworkSettings.Networks}}'
```

**Common fixes:**
```bash
# 1. Use container name, not localhost
DATABASE_URL=postgres://db:5432/mydb  # ✅
DATABASE_URL=postgres://localhost:5432/mydb  # ❌

# 2. Make sure both containers are on same network
docker network create mynet
docker run --network mynet --name db postgres
docker run --network mynet --name app myapp

# 3. Check if database is ready (depends_on doesn't wait)
# Add retry logic in your app or use wait-for-it script
```

### Debugging Commands Cheat Sheet

```bash
# See all containers (including stopped)
docker ps -a

# Check container logs
docker logs container_name
docker logs -f container_name  # Follow
docker logs --tail 50 container_name  # Last 50 lines

# Get shell inside container
docker exec -it container_name bash
docker exec -it container_name sh  # If bash not available

# Check container details
docker inspect container_name

# Check what's using a port
lsof -i :8000

# Check container resource usage
docker stats

# Check image layers
docker history image_name
```

---

## 15. Mental Model - How to Think in Docker

### The Journey: Code → Image → Container → Server

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│    CODE     │ ─► │    IMAGE    │ ─► │  CONTAINER  │ ─► │   SERVER    │
│             │    │             │    │             │    │             │
│  main.py    │    │  Blueprint  │    │   Running   │    │  In cloud   │
│  Dockerfile │    │  Frozen     │    │   Instance  │    │  Same as    │
│             │    │  Shareable  │    │   Has state │    │  your laptop│
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       │                  │                  │                  │
   You write         docker build       docker run         docker run
                                       (on your laptop)    (on server)
```

### Key Mental Models

**1. Image = Frozen Snapshot**
```
Think of an image as a frozen snapshot of:
- Operating system
- Your code
- All dependencies
- Configuration

It never changes. It's immutable.
To update, you build a NEW image.
```

**2. Container = Running Process**
```
Think of a container as:
- A running instance of an image
- Isolated environment
- Has its own filesystem, network, processes
- Can be started, stopped, deleted
- Multiple containers from one image
```

**3. Layers = Git Commits**
```
Each Dockerfile instruction = One layer
Like git commits, layers stack on each other
Unchanged layers = Cached (fast rebuilds)
Changed layer = Everything after rebuilds
```

**4. Volumes = External Hard Drive**
```
Container filesystem = temporary (deleted with container)
Volume = external storage that persists
Mount a volume = plug in external hard drive
```

### How to Reason When Something Breaks

**Step 1: Where is the problem?**
```
Build failing?     → Check Dockerfile, check files exist
Container won't start? → Check logs: docker logs container_name
App errors?        → Check logs, exec into container
Can't connect?     → Check ports, check network
```

**Step 2: Isolate the issue**
```bash
# Can I build the image?
docker build -t test .

# Can I run the container?
docker run -it test bash

# Is the app working inside?
docker exec -it container python -c "import fastapi"

# Can I reach the port?
docker exec -it container curl localhost:8000
```

**Step 3: Check the basics**
```bash
# Is the container running?
docker ps

# What are the logs saying?
docker logs container_name

# What's the container's IP/network?
docker inspect container_name

# Is the port mapped correctly?
docker port container_name
```

### The Docker Mindset

```
┌─────────────────────────────────────────────────────────────────┐
│                     OLD WAY OF THINKING                         │
├─────────────────────────────────────────────────────────────────┤
│ "Install Python on server"                                      │
│ "Install dependencies on server"                                │
│ "Configure server environment"                                  │
│ "Hope it works like my laptop"                                  │
└─────────────────────────────────────────────────────────────────┘

                              ▼

┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER WAY OF THINKING                       │
├─────────────────────────────────────────────────────────────────┤
│ "Package everything into image on my laptop"                    │
│ "Image contains Python, dependencies, config, code"             │
│ "Same image runs anywhere"                                      │
│ "Server just needs Docker installed"                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 16. Command Cheat Sheet

### Essential Commands (Use Daily)

```bash
# Build image
docker build -t name:tag .

# Run container
docker run -d -p 8000:8000 --name myapp myapp:1.0

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop myapp

# Remove container
docker rm myapp

# View logs
docker logs myapp
docker logs -f myapp  # Follow

# Execute command in container
docker exec -it myapp bash

# List images
docker images
```

### Image Commands

```bash
# Build image
docker build -t myapp:1.0 .
docker build --no-cache -t myapp:1.0 .  # Force rebuild

# Tag image
docker tag myapp:1.0 myapp:latest
docker tag myapp:1.0 username/myapp:1.0

# Push to registry
docker push username/myapp:1.0

# Pull from registry
docker pull python:3.11

# Remove image
docker rmi myapp:1.0

# Remove all unused images
docker image prune

# Show image history (layers)
docker history myapp:1.0
```

### Container Commands

```bash
# Run container
docker run myapp                    # Run in foreground
docker run -d myapp                 # Run in background
docker run -it myapp bash           # Interactive shell
docker run -p 8000:8000 myapp       # Map port
docker run -v data:/app/data myapp  # Mount volume
docker run -e KEY=value myapp       # Set environment variable
docker run --name myapp myapp:1.0   # Give container a name
docker run --rm myapp               # Remove when stopped

# Container lifecycle
docker start myapp
docker stop myapp
docker restart myapp
docker kill myapp  # Force stop

# Remove container
docker rm myapp
docker rm -f myapp  # Force remove (even if running)

# View container details
docker inspect myapp
docker port myapp
docker stats myapp
```

### Volume Commands

```bash
# Create volume
docker volume create mydata

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata

# Remove all unused volumes
docker volume prune
```

### Network Commands

```bash
# Create network
docker network create mynet

# List networks
docker network ls

# Connect container to network
docker network connect mynet myapp

# Disconnect from network
docker network disconnect mynet myapp

# Inspect network
docker network inspect mynet

# Remove network
docker network rm mynet
```

### Cleanup Commands (Safe)

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes (careful - data loss!)
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused
docker system prune

# Nuclear option - remove everything (careful!)
docker system prune -a --volumes
```

### Docker Compose Commands

```bash
# Start services
docker-compose up
docker-compose up -d  # Background

# Stop services
docker-compose down
docker-compose down -v  # Also remove volumes

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs
docker-compose logs -f app

# List services
docker-compose ps

# Execute in service
docker-compose exec app bash

# Scale service
docker-compose up -d --scale app=3
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER QUICK REFERENCE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BUILD:    docker build -t name:tag .                          │
│  RUN:      docker run -d -p 8000:8000 --name app name:tag      │
│  STOP:     docker stop app                                     │
│  LOGS:     docker logs -f app                                  │
│  SHELL:    docker exec -it app bash                            │
│  LIST:     docker ps                                           │
│  REMOVE:   docker rm app                                       │
│  CLEANUP:  docker system prune                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    DOCKERFILE STRUCTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FROM python:3.11-slim         # Base image                    │
│  WORKDIR /app                  # Set directory                 │
│  COPY requirements.txt .       # Copy deps file                │
│  RUN pip install -r ...        # Install deps                  │
│  COPY . .                      # Copy code                     │
│  EXPOSE 8000                   # Document port                 │
│  CMD ["python", "main.py"]     # Run command                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    COMMON FLAGS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  -d          Run in background (detached)                      │
│  -p 8000:80  Map host:container ports                          │
│  -v data:/x  Mount volume                                      │
│  -e KEY=val  Set environment variable                          │
│  --name app  Give container a name                             │
│  --rm        Remove when stopped                               │
│  -it         Interactive terminal                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

You now have the knowledge to:

1. ✅ Understand what Docker is and why it exists
2. ✅ Write Dockerfiles from scratch
3. ✅ Build and tag images
4. ✅ Run containers with proper flags
5. ✅ Debug when things go wrong
6. ✅ Use volumes for data persistence
7. ✅ Set up networks for multi-container apps
8. ✅ Use Docker Compose for complex setups
9. ✅ Apply production best practices

**Remember:**
- Image = Blueprint (static)
- Container = Running instance
- Dockerfile = Recipe to build image
- Volume = Persistent storage
- Network = Container communication

**When stuck:**
1. Check logs: `docker logs container`
2. Get shell: `docker exec -it container bash`
3. Inspect: `docker inspect container`
4. Check network: `docker network ls`

Happy Dockering! 🐳
