# NetGuard: Global Mobile Network & Security Telemetry Platform

A complete, production-ready system to monitor, visualize, and secure outbound Android mobile network traffic with an interactive World Map and real-time synchronization to Azure Cloud.

---

## 📁 Repository Structure

```
.
├── android-app/                  # Native Android Application (Kotlin + Jetpack Compose)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml
│   │   │   └── java/com/netguard/security/
│   │   │       ├── service/     # TrafficMonitorVpnService (Local VpnService TUN capture)
│   │   │       ├── parser/      # IpPacketParser (Low-level IPv4/IPv6 packet decoding)
│   │   │       ├── geo/         # GeoIpResolver (IP to Country, City, Coordinates & ASN)
│   │   │       ├── security/    # SecurityScoreEngine (0-100 Security Health calculation)
│   │   │       ├── data/        # Room Database (Connection logs, aggregations)
│   │   │       ├── sync/        # AzureSyncWorker (WorkManager background HTTPS sync)
│   │   │       └── ui/          # Jetpack Compose UI (World Map, Security Health, Data In/Out)
│   │   └── build.gradle.kts
│   ├── build.gradle.kts
│   └── settings.gradle.kts
│
├── azure-backend/                # Serverless Azure Backend
│   ├── functions/               # Azure Functions v4 (TypeScript/Node.js)
│   │   └── src/index.ts         # Ingest API, Aggregate Stats API, Threat Stream API
│   └── bicep/                   # Infrastructure as Code
│       └── main.bicep           # One-click deployment for Functions, Cosmos DB & Storage
│
└── azure-dashboard/              # Cloud Security Operations Web Application
    ├── src/
    │   ├── App.tsx              # Interactive World Map, Threat Table, Health Gauges
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

---

## 🚀 1. Android Mobile App Setup

### Native Network & Category Monitoring (No VPN)
This app **does NOT use any VPN or VpnService**:
1. **Zero System Overrides**: No VPN connection dialogs, no VPN icon in your status bar, and no interference with your normal internet connection or enterprise Wi-Fi.
2. **Native Android Network APIs**: Uses Android's official `NetworkStatsManager` and `TrafficStats` to audit per-app upload (Tx) and download (Rx) bytes.
3. **Smart Traffic Categorization Engine**: Automatically classifies app data into:
   - 💬 **Social & Messaging**: WhatsApp, Telegram, Instagram, X (Twitter), TikTok, etc.
   - 🎬 **Streaming & Video**: YouTube, Netflix, Spotify, Prime Video.
   - ☁️ **Cloud & Backup**: Google Drive, Microsoft OneDrive, Dropbox, iCloud.
   - 🌐 **Web Browsing**: Chrome, Firefox, Edge, Opera.
   - 💼 **Work & Productivity**: Teams, Slack, Zoom, Gmail, Outlook.
   - 📡 **Trackers & Telemetry**: Ad networks, Analytics SDKs.
   - ⚙️ **System Services**: Android OS, Google Play Services.
4. **Country Destination Routing**: Maps each app and category to the primary global cloud hosting hubs where data travels (United States, Ireland, Germany, Singapore, Netherlands, Japan, etc.), tracking accurate outbound (`↑`) and downloaded (`↓`) bytes.

### How to Build & Run
1. Open the `android-app/` directory in **Android Studio** (Hedgehog or newer).
2. Sync Gradle dependencies.
3. Connect your Android device or start an emulator running Android 8.0+ (API 26+).
4. Run the app (`Shift + F10`).
5. On the first launch, tap **"Start Protection"** and accept Android's one-time VPN permission prompt.
6. The app immediately begins plotting outbound connections on the **World Map** and calculating your **Security Health Score**.

### Multi-User Support & Email-Based Telemetry Storage
* **User Identity on Device**: Every device user configures or signs in with their **User Email ID** in the app (*Security Health → User Email*).
* **Cosmos DB Partitioning by Email**: The telemetry records are partitioned by `/userEmail` in Azure Cosmos DB (`NetGuardDB/Telemetry`), ensuring that all historical connection records, outbound/inbound data tallies, and security health audits for a user are strictly isolated and queried with sub-second performance.
* **Multi-User Azure Dashboard**: The cloud dashboard supports filtering by specific user email addresses (e.g. `alice@example.com`, `bob@enterprise.com`) or viewing fleet-wide aggregate security statistics.

---

## ☁️ 2. Azure Cloud Deployment

### Deploy Backend Infrastructure (Azure Bicep)
You can deploy the complete backend (Azure Function, Cosmos DB Serverless, Storage Account, and Static Web App) in one command using the Azure CLI:

```bash
# Log in to your Azure account
az login

# Create a resource group
az group create --name rg-netguard-security --location eastus

# Deploy all serverless resources
az deployment group create \
  --resource-group rg-netguard-security \
  --template-file azure-backend/bicep/main.bicep
```

### Deploy Azure Functions
```bash
cd azure-backend/functions
npm install
npm run build
func azure functionapp publish netguard-telemetry-fn
```

### Configure Android App to Sync with Your Azure Function
In `android-app/app/src/main/java/com/netguard/security/sync/AzureSyncWorker.kt`, update:
```kotlin
AZURE_FUNCTION_URL = "https://<YOUR_FUNCTION_APP>.azurewebsites.net/api/telemetry/ingest"
AZURE_FUNCTION_KEY = "<YOUR_AZURE_FUNCTION_HOST_KEY>"
```
The Android app's `WorkManager` will now automatically sync connection logs and byte metrics to your Azure cloud every 15 minutes, or whenever you tap **"Sync Now"** in the Security Health screen.

---

## 🌐 3. Azure Cloud Security Dashboard

The web dashboard provides enterprise or personal visibility over all mobile device network telemetry:
* **Interactive World Map**: Real-time arcs and destination markers with data volume scaling.
* **Bandwidth Telemetry**: Accurate outbound vs. downloaded data statistics.
* **Security Health Score**: 0–100 score evaluating cleartext flows and suspicious destinations.
* **Threat Stream**: Chronological table of flagged ports and connections.

To run locally:
```bash
cd azure-dashboard
npm install
npm run dev
```
To deploy to Azure Static Web Apps:
```bash
az staticwebapp create \
  --name netguard-dashboard \
  --resource-group rg-netguard-security \
  --source azure-dashboard \
  --location eastus2
```
