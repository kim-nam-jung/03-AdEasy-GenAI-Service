# AdEasy GenAI Service - L4 GPU Deployment Guide

This guide explains how to deploy the service on a remote server with an L4 GPU (e.g., Google Cloud, AWS, RunPod).

## 0. GCP Server Setup (Beginner's Guide)

If you are new to Google Cloud Platform (GCP), follow this step-by-step guide to get your server running.

### Step 1: Request Quota (CRITICAL)
New accounts often have **0 GPU quota**. You must request it before creating an instance.
1.  Go to [GCP Console > IAM & Admin > Quotas](https://console.cloud.google.com/iam-admin/quotas).
2.  Filter by: `Service: Compute Engine API`, `Limit name: NVIDIA L4 GPUs`.
3.  Select the region you want (e.g., `us-central1` or `asia-northeast3`).
4.  Click **EDIT QUOTAS** -> Enter `1` -> Submit Request. *(Approval usually takes minutes to hours).*

### Step 2: Create VM Instance
1.  Go to **Compute Engine > VM Instances** -> Click **Create Instance**.
2.  **Name**: `adeasy-server`.
3.  **Region**: Select the region where you have L4 quota.
4.  **Machine Configuration**:
    *   **Series**: `G2`
    *   **Machine type**: `g2-standard-4` (4 vCPUs, 1 L4 GPU).
5.  **Boot Disk** (SAVE TIME HERE):
    *   Click **Change**.
    *   **OS**: `Deep Learning on Linux`.
    *   **Version**: `Deep Learning VM with CUDA 11.8 M116` (or newer).
    *   *Why? This image has Nvidia Drivers and Docker pre-installed.*
6.  **Firewall**: Check `Allow HTTP traffic` and `Allow HTTPS traffic`.
7.  **Advanced > Networking**:
    *   **Network tags**: Add `adeasy-server`.
8.  Click **CREATE**.

### Step 3: Open Firewall Ports (3000, 8000)
1.  Search **VPC Network > Firewall**.
2.  Click **CREATE FIREWALL RULE**.
3.  **Name**: `allow-adeasy`.
4.  **Target tags**: `adeasy-server` (matches the tag you added above).
5.  **Source IPv4 ranges**: `0.0.0.0/0` (Allow all) OR your specific IP.
6.  **Protocols and ports**: `tcp:3000,8000`.
7.  Click **CREATE**.

### Step 3.5: SSH Connection
*   Click the **SSH** button next to your instance in the VM list to open a browser terminal.
*   OR use `gcloud compute ssh` commands from your local terminal (see Section 7).

---

## 1. Prerequisites (Remote Server)

Ensure the server has the following installed:

1.  **NVIDIA Drivers**: Verify with `nvidia-smi`.
2.  **Docker**: [Install Guide](https://docs.docker.com/engine/install/ubuntu/)
3.  **NVIDIA Container Toolkit**: **Crucial** for Docker to access the GPU.
    ```bash
    # Install
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # Configure Docker
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    ```

## 2. Setup Project

1.  **Clone Repository**:
    ```bash
    git clone <your-repo-url> adeasy
    cd adeasy
    ```

2.  **Environment Variables**:
    Create `.env` inside `backend/`:
    ```bash
    cp backend/.env.example backend/.env
    nano backend/.env
    ```
    *   Set `OPENAI_API_KEY` (Required for Supervisor Agent).
    *   Set `X_API_KEY` (Optional, defaults to `adeasy-secret-key`).

3.  **Model Preparation**:
    The service will attempt to download models automatically on first run, but for L4 (24GB VRAM), ensure you have enough disk space (~50GB+ for models).
    *   Models will be cached in `./models` directory (mounted via Docker volume).

## 3. Deploy

Run with Docker Compose:

```bash
docker-compose up -d --build
```

*   **View Logs**: `docker-compose logs -f backend`

## 4. Accessing the Service

### Option A: SSH Tunneling (Recommended for quick test)
If the server doesn't have a public IP with open ports, tunnel the ports to your local machine:

```bash
# Run this on your LOCAL machine
ssh -L 3000:localhost:3000 -L 8000:localhost:8000 user@your-l4-server-ip
```
Then access:
*   **Frontend**: http://localhost:3000
*   **API Docs**: http://localhost:8000/docs

### Option B: Public IP
If ports 3000 and 8000 are open in the firewall (Security Group):
*   **Frontend**: http://<server-ip>:3000
*   **API**: Change `frontend/Dockerfile` or rebuild frontend with `VITE_API_URL=http://<server-ip>:8000`.

## 5. L4 Optimization Tips

The **L4 GPU** has **24GB VRAM**.
*   **LTX-Video (13B)**: Should fit comfortably with the existing `VRAMManager` logic which unloads models between steps.
*   **Performance**: The `Supervisor` agent adds a small latency for reflection, but this is negligible compared to video generation time.
*   **Monitoring**: Run `watch -n 1 nvidia-smi` on the server to monitor VRAM usage during the pipeline.

## 6. Testing

1.  Open the Frontend.
2.  Upload a test image (e.g., a product photo).
3.  Enter a prompt.
4.  Click **Generate**.
5.  Watch the **Real-time Reflection Log**. It should stream the Supervisor's thoughts.
    *   *If it says "Connecting...", check if WebSocket port (8000) is accessible.*

## 7. Development & Editing (How to Modify Code)

### Recommended: VS Code Remote - SSH
The most efficient way to edit code on the L4 server is using VS Code's "Remote - SSH" extension.

#### General / AWS / RunPod
1.  **Install Extension**: In VS Code, install **Remote - SSH**.
2.  **Connect**:
    *   Press `F1` -> Type `Remote-SSH: Connect to Host...`
    *   Enter `user@your-l4-server-ip`.

#### Google Cloud Platform (GCP) Specific
GCP requires SSH keys managed by gcloud or metadata. The easiest way:

1.  **Install Cloud SDK**: Ensure `gcloud` CLI is installed on your local machine.
2.  **Generate Config**: Run this command locally to generate an SSH config entry:
    ```bash
    gcloud compute ssh <INSTANCE_NAME> --project <PROJECT_ID> --zone <ZONE> --dry-run
    ```
    *   Copy the output command (it starts with `/usr/bin/ssh ...`).
3.  **Configure VS Code**:
    *   Press `F1` -> `Remote-SSH: Open Configuration File...` -> Select your config file.
    *   Add a new host entry:
        ```text
        Host gcp-l4
            HostName <EXTERNAL_IP>
            User <YOUR_GCP_USERNAME>
            IdentityFile ~/.ssh/google_compute_engine
        ```
    *   *Note: `gcloud compute ssh` usually creates keys in `~/.ssh/google_compute_engine` by default upon first login.*
4.  **Connect**: `F1` -> `Remote-SSH: Connect to Host...` -> Select `gcp-l4`.
3.  **Open Folder**: Once connected, open the `/home/user/adeasy` folder.
    *   You can now edit files directly on the server as if they were local.
4.  **Hot Reload**:
    *   Since we run with `docker-compose` and volumes (`- ./backend:/app`), changes to Python files will **automatically reload** the backend server (FastAPI has `--reload` on).
    *   Frontend changes (React) will also Hot Module Replace (HMR) instantly if port 3000 is forwarded.

### Alternative: Git Workflow
If you prefer editing locally:
1.  **Edit** code on your local machine.
2.  **Commit & Push**: `git push origin main`.
3.  **Pull on Server**: SSH into server and run `git pull origin main`.
4.  **Restart** (if needed): `docker-compose restart backend`.

