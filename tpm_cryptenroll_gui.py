import sys
import subprocess
import json
import tempfile
import os
import shlex
import shutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QRadioButton, QPushButton,
                             QMessageBox, QInputDialog, QLineEdit,
                             QDialog, QTextEdit, QLabel, QFrame, QProgressBar,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox,
                             QTreeWidgetItemIterator)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QLocale, QTimer
from PyQt6.QtGui import QFont, QIcon

# --- GESTION DES LANGUES (i18n) ---
sys_lang = QLocale.system().name()[:2]
LANG = 'fr' if sys_lang == 'fr' else 'en'

TR = {
    'fr': {
        'check_title': "Vérification du système",
        'check_wait': "Analyse des composants en cours...",
        'check_os': "Système d'exploitation Linux",
        'check_crypt': "Outil systemd-cryptenroll",
        'check_polkit': "Service Polkit (pkexec)",
        'check_lsblk': "Outil d'analyse disque (lsblk)",
        'check_sb': "Secure Boot activé",
        'check_ok': "Système compatible !",
        'check_fail': "Incompatibilité détectée",
        'btn_continue': "Continuer",
        'desc': "Sécurisez facilement le déchiffrement de vos disques LUKS \navec la puce TPM de votre ordinateur.",
        'step1': "1. Sélectionnez vos disques LUKS",
        'step2': "2. Choisissez la méthode d'enrôlement",
        'cols': ["Périphérique", "Système", "Montage", "Étiquette", "Taille"],
        'btn_inspect': "🔍 Inspecter les slots du/des disque(s)",
        'radio_simple': "Enrôlement TPM2 Simple",
        'radio_pin': "Enrôlement TPM2 avec code PIN",
        'info_pcr': "ℹ️ Info : Cet outil enrôle le TPM avec le PCR 7 par défaut\n(vérifie l'intégrité du Secure Boot au démarrage).",
        'wipe_check': "⚠️ Effacer les emplacements TPM2 existants (Recommandé)",
        'btn_enroll': "🛡️ Démarrer l'enrôlement",
        'no_luks': "Aucun disque contenant du LUKS n'a été trouvé.",
        'unknown_model': "Modèle inconnu",
        'encrypted': "LUKS [Chiffré]",
        'warn_sel_inspect': "Veuillez sélectionner au moins une partition LUKS à inspecter.",
        'warn_sel_enroll': "Veuillez sélectionner au moins une partition LUKS (cadenas).",
        'info_title': "État actuel des slots LUKS",
        'close': "Fermer",
        'auth_title': "Authentification LUKS",
        'auth_msg': "Entrez le mot de passe actuel de vos disques LUKS :",
        'pin_title': "Configuration PIN TPM2",
        'pin_msg': "Choisissez le nouveau code PIN de déverrouillage TPM :",
        'prog_title': "Enrôlement en cours",
        'prog_req': "Demande des droits administrateur...",
        'prog_config': "Configuration de",
        'prog_done': "Enrôlement terminé !",
        'success': "Succès",
        'success_msg': "L'enrôlement a été effectué avec succès sur tous les disques.",
        'error': "Erreur",
        'error_msg': "L'opération a échoué.\n\nDétails :\n",
        'work_ok': "Opération terminée avec succès.",
        'work_err': "Erreur lors de l'exécution (voir console)."
    },
    'en': {
        'check_title': "System Check",
        'check_wait': "Scanning components...",
        'check_os': "Linux Operating System",
        'check_crypt': "systemd-cryptenroll tool",
        'check_polkit': "Polkit service (pkexec)",
        'check_lsblk': "Disk analysis tool (lsblk)",
        'check_sb': "Secure Boot enabled",
        'check_ok': "System compatible!",
        'check_fail': "Incompatibility detected",
        'btn_continue': "Continue",
        'desc': "Easily secure the decryption of your LUKS disks \nusing your computer's TPM chip.",
        'step1': "1. Select your LUKS disks",
        'step2': "2. Choose the enrollment method",
        'cols': ["Device", "System", "Mount", "Label", "Size"],
        'btn_inspect': "🔍 Inspect slots of selected disk(s)",
        'radio_simple': "Simple TPM2 Enrollment",
        'radio_pin': "TPM2 Enrollment with PIN code",
        'info_pcr': "ℹ️ Info: This tool enrolls the TPM using PCR 7 by default\n(verifies Secure Boot integrity at startup).",
        'wipe_check': "⚠️ Wipe existing TPM2 slots (Recommended)",
        'btn_enroll': "🛡️ Start Enrollment",
        'no_luks': "No disk containing LUKS was found.",
        'unknown_model': "Unknown model",
        'encrypted': "LUKS [Encrypted]",
        'warn_sel_inspect': "Please select at least one LUKS partition to inspect.",
        'warn_sel_enroll': "Please select at least one LUKS partition (padlock).",
        'info_title': "Current state of LUKS slots",
        'close': "Close",
        'auth_title': "LUKS Authentication",
        'auth_msg': "Enter the current password for your LUKS disks:",
        'pin_title': "TPM2 PIN Configuration",
        'pin_msg': "Choose the new TPM unlocking PIN code:",
        'prog_title': "Enrollment in progress",
        'prog_req': "Requesting administrator rights...",
        'prog_config': "Configuring",
        'prog_done': "Enrollment finished!",
        'success': "Success",
        'success_msg': "Enrollment completed successfully on all selected disks.",
        'error': "Error",
        'error_msg': "The operation failed.\n\nDetails:\n",
        'work_ok': "Operation finished successfully.",
        'work_err': "Execution error (see console)."
    }
}
T = TR[LANG]

# --- Popup de Vérification au démarrage ---
class CompatibilityDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T['check_title'])
        self.setFixedSize(400, 320)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)

        self.title_lbl = QLabel(T['check_wait'])
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(self.title_lbl)

        # Liste des composants à vérifier
        self.checks = {
            'os': T['check_os'],
            'crypt': T['check_crypt'],
            'polkit': T['check_polkit'],
            'lsblk': T['check_lsblk'],
            'sb': T['check_sb']
        }
        self.labels = {}

        for key, text in self.checks.items():
            h_layout = QHBoxLayout()
            lbl_status = QLabel("⏳") # Statut en attente
            lbl_name = QLabel(text)
            h_layout.addWidget(lbl_status)
            h_layout.addWidget(lbl_name)
            h_layout.addStretch()
            layout.addLayout(h_layout)
            self.labels[key] = lbl_status

        self.btn_next = QPushButton(T['btn_continue'])
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self.accept)
        layout.addWidget(self.btn_next, alignment=Qt.AlignmentFlag.AlignCenter)

        # Lancer la vérification après un court délai pour l'effet visuel
        QTimer.singleShot(800, self.run_checks)

    def run_checks(self):
        results = []

        # 1. OS
        is_linux = sys.platform.startswith('linux')
        self.labels['os'].setText("✅" if is_linux else "❌")
        results.append(is_linux)

        # 2. Cryptenroll
        has_crypt = shutil.which("systemd-cryptenroll") is not None
        self.labels['crypt'].setText("✅" if has_crypt else "❌")
        results.append(has_crypt)

        # 3. Polkit
        has_pk = shutil.which("pkexec") is not None
        self.labels['polkit'].setText("✅" if has_pk else "❌")
        results.append(has_pk)

        # 4. lsblk
        has_ls = shutil.which("lsblk") is not None
        self.labels['lsblk'].setText("✅" if has_ls else "❌")
        results.append(has_ls)

        # 5. Secure Boot
        has_sb = False
        try:
            res = subprocess.run(["mokutil", "--sb-state"], capture_output=True, text=True)
            if "enabled" in res.stdout.lower():
                has_sb = True
        except FileNotFoundError:
            # Fallback si mokutil n'est pas installé
            try:
                res = subprocess.run(["bootctl", "status"], capture_output=True, text=True)
                if "Secure Boot: enabled" in res.stdout:
                    has_sb = True
            except FileNotFoundError:
                pass

        self.labels['sb'].setText("✅" if has_sb else "❌")
        results.append(has_sb)

        if all(results):
            self.title_lbl.setText(f"<font color='green'>{T['check_ok']}</font>")
            self.btn_next.setEnabled(True)
            self.btn_next.setStyleSheet("background-color: #2b5797; color: white; padding: 5px 20px;")
            QTimer.singleShot(3000, self.accept)
        else:
            self.title_lbl.setText(f"<font color='red'>{T['check_fail']}</font>")
            self.btn_next.setText(T['close'])
            self.btn_next.setEnabled(True)
            self.btn_next.clicked.disconnect()
            self.btn_next.clicked.connect(sys.exit)


class EnrollmentWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        try:
            process = subprocess.Popen(["pkexec", self.script_path],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       text=True)
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line.startswith("PROGRESS:"):
                    val = int(line.replace("PROGRESS:", "").strip())
                    self.progress_signal.emit(val)
                elif line.startswith("STATUS:"):
                    txt = line.replace("STATUS:", "").strip()
                    self.status_signal.emit(txt)
            process.stdout.close()
            process.wait()
            if process.returncode == 0:
                self.finished_signal.emit(True, T['work_ok'])
            else:
                self.finished_signal.emit(False, T['work_err'])
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class CryptEnrollApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPM Enrollment GUI")

        self.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 14px; margin-top: 15px; border: 1px solid #888888; border-radius: 6px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
            QPushButton { padding: 8px; border-radius: 4px; }
            QTreeView::item { padding: 4px 0px; }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.setup_header()

        self.disks_group = QGroupBox(T['step1'])
        self.disks_layout = QVBoxLayout()
        self.disk_tree = QTreeWidget()
        self.disk_tree.setHeaderLabels(T['cols'])
        self.disk_tree.setAlternatingRowColors(True)
        self.disk_tree.setIndentation(20)
        self.disk_tree.headerItem().setTextAlignment(4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.disk_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            self.disk_tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.disks_layout.addWidget(self.disk_tree)
        self.luks_items = []
        self.populate_luks_disks()

        self.btn_check_slots = QPushButton(T['btn_inspect'])
        self.btn_check_slots.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_slots.clicked.connect(self.show_disk_info)
        self.disks_layout.addWidget(self.btn_check_slots)
        self.disks_group.setLayout(self.disks_layout)
        self.layout.addWidget(self.disks_group)

        self.options_group = QGroupBox(T['step2'])
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.radio_tpm2_simple = QRadioButton(T['radio_simple'])
        self.radio_tpm2_pin = QRadioButton(T['radio_pin'])
        self.radio_tpm2_simple.setChecked(True)
        self.options_layout.addWidget(self.radio_tpm2_simple)
        self.options_layout.addWidget(self.radio_tpm2_pin)
        self.pcr_info_label = QLabel(T['info_pcr'])
        self.pcr_info_label.setStyleSheet("color: #666666; font-size: 12px; font-style: italic; margin-left: 20px;")
        self.options_layout.addWidget(self.pcr_info_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.options_layout.addWidget(line)

        self.check_wipe = QCheckBox(T['wipe_check'])
        self.check_wipe.setStyleSheet("color: #d9534f; font-weight: bold;")
        self.check_wipe.setChecked(True)
        self.options_layout.addWidget(self.check_wipe)
        self.options_group.setLayout(self.options_layout)
        self.layout.addWidget(self.options_group)

        self.btn_enroll = QPushButton(T['btn_enroll'])
        self.btn_enroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enroll.clicked.connect(self.start_enrollment)
        self.btn_enroll.setStyleSheet("QPushButton { font-weight: bold; font-size: 16px; padding: 12px; background-color: #2b5797; color: white; } QPushButton:hover { background-color: #1e3f6e; }")
        self.layout.addWidget(self.btn_enroll)

        self.temp_pass_path = None
        self.temp_script_path = None

        self.setMinimumWidth(700)

    # --- NOUVEAUTÉ : Événement déclenché quand la fenêtre est affichée ---
    def showEvent(self, event):
        super().showEvent(event)
        # On attend quelques millisecondes que Qt ait fini de dessiner l'interface
        # avant de calculer précisément la hauteur.
        QTimer.singleShot(50, self.ajuster_hauteur_arbre)

    def ajuster_hauteur_arbre(self):
        # On force la désactivation de la barre de défilement verticale
        self.disk_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        hauteur_requise = self.disk_tree.header().height()
        hauteur_requise += self.disk_tree.frameWidth() * 2 # Bordures du tableau

        it = QTreeWidgetItemIterator(self.disk_tree)
        while it.value():
            rect = self.disk_tree.visualItemRect(it.value())
            h = rect.height()
            hauteur_requise += (h if h > 0 else 28)
            it += 1

        # On applique la hauteur exacte au widget + une petite marge de sécurité de 5 pixels
        self.disk_tree.setMinimumHeight(hauteur_requise + 5)

        # On ajuste enfin la taille globale de l'application
        self.adjustSize()

    def setup_header(self):
        header_layout = QVBoxLayout()
        title_label = QLabel("TPM Enrollment GUI")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        desc_label = QLabel(T['desc'])
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: gray;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        self.layout.addLayout(header_layout)

    def populate_luks_disks(self):
        try:
            cmd = ["lsblk", "--json", "-o", "PATH,KNAME,PKNAME,TYPE,FSTYPE,SIZE,LABEL,MOUNTPOINTS"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            all_devices = []
            def flatten_devices(devices):
                for dev in devices:
                    all_devices.append(dev)
                    if "children" in dev: flatten_devices(dev["children"])
            flatten_devices(data.get("blockdevices", []))
            children_map = {}
            for dev in all_devices:
                pk = dev.get("pkname")
                if pk:
                    if pk not in children_map: children_map[pk] = []
                    children_map[pk].append(dev)
            roots = [d for d in all_devices if d.get("type") == "disk"]
            def has_luks(kname):
                dev = next((d for d in all_devices if d.get("kname") == kname), None)
                if not dev: return False
                if dev.get("fstype") == "crypto_LUKS": return True
                for child in children_map.get(kname, []):
                    if has_luks(child.get("kname")): return True
                return False
            has_any_luks = False
            for root in roots:
                root_kname = root.get("kname")
                if not has_luks(root_kname): continue
                has_any_luks = True
                r_path = root.get("path", "Inconnu")
                r_size = root.get("size", "??")
                model = T['unknown_model']
                try:
                    cmd_mod = ["lsblk", "-s", "-n", "-o", "MODEL", r_path]
                    res_mod = subprocess.run(cmd_mod, capture_output=True, text=True)
                    mods = [m.strip() for m in res_mod.stdout.split('\n') if m.strip()]
                    if mods: model = mods[-1]
                except: pass
                parent_item = QTreeWidgetItem(self.disk_tree)
                parent_item.setText(0, f"💽 {model} ({r_path})")
                parent_item.setText(4, r_size)
                font = parent_item.font(0); font.setBold(True); font.setPointSize(10)
                for i in range(5): parent_item.setFont(i, font)
                parent_item.setTextAlignment(4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                def build_tree_nodes(parent_widget, pkname):
                    for child in children_map.get(pkname, []):
                        c_path = child.get("path", "Inconnu"); c_fstype = child.get("fstype", ""); c_size = child.get("size", "??"); c_type = child.get("type", ""); c_kname = child.get("kname")
                        mounts = child.get("mountpoints", []); l_mount = ", ".join([m for m in mounts if m and str(m).strip()])
                        item = QTreeWidgetItem(parent_widget)
                        item.setTextAlignment(4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        if c_fstype == "crypto_LUKS":
                            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(0, Qt.CheckState.Unchecked)
                            item.setText(0, f"🔒 {c_path}"); item.setText(1, T['encrypted'])
                            font = item.font(0); font.setBold(True); [item.setFont(i, font) for i in range(5)]
                            item.setData(0, Qt.ItemDataRole.UserRole, c_path); self.luks_items.append(item)
                        else:
                            icn = "📄" if c_type == "part" else "🔓" if c_type == "crypt" else "📦"
                            item.setText(0, f"{icn} {c_path}"); item.setText(1, c_fstype)
                            font = item.font(0); font.setItalic(True); [item.setFont(i, font) for i in range(5)]
                        item.setText(2, l_mount); item.setText(3, child.get("label", "")); item.setText(4, c_size)
                        build_tree_nodes(item, c_kname)
                build_tree_nodes(parent_item, root_kname)
            if not has_any_luks:
                QTreeWidgetItem(self.disk_tree).setText(0, T['no_luks'])

            # Déploie automatiquement tout l'arbre
            self.disk_tree.expandAll()

        except Exception as e:
            QMessageBox.critical(self, T['error'], str(e))

    def get_selected_disks(self):
        return [item.data(0, Qt.ItemDataRole.UserRole) for item in self.luks_items if item.checkState(0) == Qt.CheckState.Checked]

    def show_disk_info(self):
        selected = self.get_selected_disks()
        if not selected: QMessageBox.warning(self, "Attention", T['warn_sel_inspect']); return
        script_commands = ["#!/bin/bash"]
        for disk in selected: script_commands.extend([f"echo '=============== {disk} ==============='", f"cryptsetup luksDump {disk}", "echo ''"])
        fd, path = tempfile.mkstemp(dir="/dev/shm", prefix="Outil_Securite_Disque_", text=True)
        try:
            with os.fdopen(fd, 'w') as f: f.write("\n".join(script_commands))
            os.chmod(path, 0o755)
            res = subprocess.run(["pkexec", path], capture_output=True, text=True)
            self.display_info_dialog(res.stdout + (f"\nErrors:\n{res.stderr}" if res.stderr else ""))
        except Exception as e: QMessageBox.critical(self, T['error'], str(e))
        finally:
            if os.path.exists(path): os.remove(path)

    def display_info_dialog(self, text):
        d = QDialog(self); d.setWindowTitle(T['info_title']); d.resize(650, 550)
        l = QVBoxLayout(d); te = QTextEdit(); te.setReadOnly(True); te.setPlainText(text)
        te.setFont(QFont("monospace", 10)); l.addWidget(te)
        b = QPushButton(T['close']); b.clicked.connect(d.accept); l.addWidget(b); d.exec()

    def start_enrollment(self):
        selected = self.get_selected_disks()
        if not selected: QMessageBox.warning(self, "Attention", T['warn_sel_enroll']); return
        pwd, ok = QInputDialog.getText(self, T['auth_title'], T['auth_msg'], QLineEdit.EchoMode.Password)
        if not ok or not pwd: return
        pin = None
        if self.radio_tpm2_pin.isChecked():
            pin, ok = QInputDialog.getText(self, T['pin_title'], T['pin_msg'], QLineEdit.EchoMode.Password)
            if not ok or not pin: return
        self.process_batch_enrollment(selected, pwd, pin)

    def process_batch_enrollment(self, disks, pwd, pin):
        self.btn_enroll.setEnabled(False)
        fd_p, self.temp_pass_path = tempfile.mkstemp(dir="/dev/shm", text=True)
        fd_s, self.temp_script_path = tempfile.mkstemp(dir="/dev/shm", prefix="Enrolement_TPM_Disque_", text=True)
        os.chmod(self.temp_pass_path, 0o600)
        with os.fdopen(fd_p, 'w') as f: f.write(pwd)
        script = ["#!/bin/bash", "set -e"]
        if pin: script.append(f'export NEWPIN={shlex.quote(pin)}')
        for i, d in enumerate(disks):
            script.append(f'echo "PROGRESS: {int((i/len(disks))*100)}"')
            script.append(f'echo "STATUS: {T["prog_config"]} {d}..."')
            cmd = f"systemd-cryptenroll --unlock-key-file={self.temp_pass_path}"
            if self.check_wipe.isChecked(): cmd += " --wipe-slot=tpm2"
            cmd += " --tpm2-device=auto" + (" --tpm2-with-pin=yes" if pin else "") + f' "{d}"'
            script.append(cmd)
        script.append('echo "PROGRESS: 100"'); script.append(f'echo "STATUS: {T["prog_done"]}"')
        with os.fdopen(fd_s, 'w') as f: f.write("\n".join(script))
        os.chmod(self.temp_script_path, 0o755)
        self.progress_dialog = QDialog(self); self.progress_dialog.setWindowTitle(T['prog_title']); self.progress_dialog.resize(350, 100); self.progress_dialog.setModal(True)
        pl = QVBoxLayout(self.progress_dialog); self.status_label = QLabel(T['prog_req']); self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter); pl.addWidget(self.status_label)
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 100); pl.addWidget(self.progress_bar)
        self.worker = EnrollmentWorker(self.temp_script_path); self.worker.progress_signal.connect(self.progress_bar.setValue); self.worker.status_signal.connect(self.status_label.setText); self.worker.finished_signal.connect(self.on_enrollment_finished)
        self.worker.start(); self.progress_dialog.exec()

    def on_enrollment_finished(self, success, msg):
        self.progress_dialog.accept(); self.btn_enroll.setEnabled(True)
        if self.temp_pass_path and os.path.exists(self.temp_pass_path): os.remove(self.temp_pass_path)
        if self.temp_script_path and os.path.exists(self.temp_script_path): os.remove(self.temp_script_path)
        if success: QMessageBox.information(self, T['success'], T['success_msg'])
        else: QMessageBox.critical(self, T['error'], f"{T['error_msg']}{msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ÉTAPE 1 : Affichage du popup de compatibilité
    compat_checker = CompatibilityDialog()
    if compat_checker.exec() == QDialog.DialogCode.Accepted:
        # ÉTAPE 2 : Si accepté, on lance l'application
        window = CryptEnrollApp()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
