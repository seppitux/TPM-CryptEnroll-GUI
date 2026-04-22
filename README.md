# 🛡️ TPM Cryptenroll GUI


[**Français**](#français) | [**English**](#english)

---

<a name="français"></a>
## 🇫🇷 Français

### 📋 Présentation
Cette interface graphique (GUI) simplifie l'utilisation de `systemd-cryptenroll` pour sécuriser le déchiffrement de vos disques LUKS via la puce **TPM 2.0**. Elle permet de configurer le déverrouillage automatique au démarrage tout en s'assurant que l'intégrité du système est préservée via le **Secure Boot** (PCR 7).

### ✨ Caractéristiques
* **Détection automatique** : Scanne et identifie vos partitions chiffrées LUKS.
* **Inspection des slots** : Visualisez l'état des emplacements de clés avant modification.
* **Modes d'enrôlement** : Supporte l'enrôlement TPM simple ou avec code PIN.
* **Sécurité** : Option pour effacer les anciens slots TPM2 afin d'éviter les conflits.
* **Multilingue** : Interface automatique en Français ou Anglais selon la langue du système.

### 🚀 Installation & Utilisation

#### Option 1 : Utiliser le binaire (Recommandé)
1. Téléchargez le fichier exécutable depuis l'onglet [**Releases**](../../releases).
2. Donnez-lui les droits d'exécution :
   ```bash
   chmod +x tpm-cryptenroll-gui


   # 🛡️ TPM Cryptenroll GUI

[**Français**](#français) | [**English**](#english)

---

<a name="english"></a>
## 🇬🇧 English

### 📋 Overview
This Graphical User Interface (GUI) simplifies the use of `systemd-cryptenroll` to secure the decryption of your LUKS disks using your computer's **TPM 2.0** chip. It allows you to configure automatic unlocking at boot while ensuring system integrity through **Secure Boot** (PCR 7).

### ✨ Features
* **Automatic Detection**: Scans and identifies your LUKS-encrypted partitions.
* **Slot Inspection**: View the state of your LUKS key slots before making any changes.
* **Enrollment Modes**: Supports both simple TPM enrollment and TPM with a PIN code.
* **Security**: Option to wipe existing TPM2 slots to prevent conflicts.
* **Multilingual**: Automatic interface in French or English based on your system language.

### 🚀 Installation & Usage

#### Option 1: Use the Binary (Recommended)
1. Download the executable file from the [**Releases**](../../releases) tab.
2. Grant execution permissions:
   ```bash
   chmod +x tpm-cryptenroll-gui
