// Auto-fermeture des alertes après 5 secondes
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('hiding');
            setTimeout(() => {
                alert.remove();
            }, 400);
        }, 5000);
    });
});

// Menu Toggle
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');

menuToggle.addEventListener('click', () => {
    if (window.innerWidth > 768) {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
    } else {
        sidebar.classList.toggle('open');
    }
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});
        
// Modal Functions
function openModalLogout() {
    const modal = document.getElementById('modalLogout');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModalLogout() {
    const modal = document.getElementById('modalLogout');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}



// Close modal when clicking outside
document.getElementById('ModalAddMesse').addEventListener('click', (e) => {
    if (e.target.id === 'ModalAddMesse') {
        closeModal();
    }
});
/* ---- AJOUT ---- */
function openModalAddMesse() {
    document.getElementById("modalAddMesse").style.display = "flex";
}
function closeModalAddMesse() {
    document.getElementById("modalAddMesse").style.display = "none";
}

/* ---- MODIFICATION ---- */
function openModalEditMesse(id, jour, heure, type, fete) {
    // Mettre à jour l'action du formulaire avec l'id de la messe
    document.getElementById("formEditMesse").action = "update_messe/" + id + "/";

    // Remplir les champs avec les valeurs actuelles
    document.getElementById("editJour").value = jour;
    document.getElementById("editHeure").value = heure;
    document.getElementById("editType").value = type;
    document.getElementById("editFete").value = fete;

    document.getElementById("modalEditMesse").style.display = "flex";
}
function closeModalEditMesse() {
    document.getElementById("modalEditMesse").style.display = "none";
}

/* ---- SUPPRESSION ---- */
function openModalDeleteMesse(id) {
    document.getElementById("deleteMesseLink").href = "delete_messe/" + id + "/";
    document.getElementById("modalDeleteMesse").style.display = "flex";
}
function closeModalDeleteMesse() {
    document.getElementById("modalDeleteMesse").style.display = "none";
}

/* ---- Fermeture en cliquant sur l'overlay ---- */
document.querySelectorAll(".modal-overlay").forEach(function(overlay) {
    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            overlay.style.display = "none";
        }
    });
});



/* ---- AJOUT DEMANDE ---- */
function openModalDemande() {
    var modal = document.getElementById("modalDemande");
    if (modal) modal.style.display = "flex";
}

function closeModalDemande() {
    var modal = document.getElementById("modalDemande");
    if (modal) modal.style.display = "none";
}

/* ---- MODIFICATION DEMANDE ---- */
function openModalEditIntention(id, demandeur, intention, categorie, horaireId, date, telephone) {
    console.log("Opening modal for ID:", id); // Pour déboguer
    
    // Afficher le modal
    var modal = document.getElementById("modalEditIntention");
    if (!modal) {
        console.error("Modal edit not found!");
        return;
    }
    modal.style.display = "flex";
    
    // Mettre à jour l'action du formulaire
    var form = document.getElementById("editIntentionForm");
    if (form) {
        // Utilisez l'URL directement au lieu du tag Django
        form.action = "update_intention/" + id + "/";
        console.log("Form action set to:", form.action);
    }
    
    // Remplir les champs
    var demandeurField = document.getElementById("editDemandeur");
    var intentionField = document.getElementById("editIntention");
    var categorieField = document.getElementById("editcategorie");
    var dateField = document.getElementById("editDate");
    var telephoneField = document.getElementById("editTelephone");
    var horaireField = document.getElementById("editInfoMesse");
    
    if (demandeurField) demandeurField.value = demandeur || '';
    if (intentionField) intentionField.value = intention || '';
    if (dateField) dateField.value = date || '';
    if (telephoneField) telephoneField.value = telephone || '';
    if (horaireField && horaireId) horaireField.value = horaireId;
    if (categorieField) categorieField.value = categorie || '';
}

function closeModalEditIntention() {
    var modal = document.getElementById("modalEditIntention");
    if (modal) modal.style.display = "none";
}

/* ---- SUPPRESSION DEMANDE ---- */
function openModalDeleteIntention(id) {
    console.log("Opening delete modal for ID:", id); // Pour déboguer
    
    var modal = document.getElementById("modalDeleteIntention");
    if (!modal) {
        console.error("Modal delete not found!");
        return;
    }
    
    var deleteLink = document.getElementById("deleteIntentionLink");
    if (deleteLink) {
        deleteLink.href = "delete_intention/" + id + "/";
        console.log("Delete link set to:", deleteLink.href);
    }
    
    modal.style.display = "flex";
}

function closeModalDeleteIntention() {
    var modal = document.getElementById("modalDeleteIntention");
    if (modal) modal.style.display = "none";
}



/* ---- AJOUT ---- */
function openModalAddUser() {
    document.getElementById("modalAddUser").style.display = "flex";
}
function closeModalAddUser() {
    document.getElementById("modalAddUser").style.display = "none";
}

/* ---- SUPPRESSION ---- */
function openModalDeleteUser(id, username) {
    document.getElementById("deleteUserName").textContent = username;
    document.getElementById("deleteUserLink").href = "{% url 'delete_users' 0 %}".replace("0", id);
    document.getElementById("modalDeleteUser").style.display = "flex";
}
function closeModalDeleteUser() {
    document.getElementById("modalDeleteUser").style.display = "none";
}

/* ---- Afficher/Masquer mot de passe ---- */
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon  = btn.querySelector('i');
    if (input.type === "password") {
        input.type = "text";
        icon.className = "ri-eye-off-line";
    } else {
        input.type = "password";
        icon.className = "ri-eye-line";
    }
}

/* ---- Fermeture overlay ---- */
document.querySelectorAll(".modal-overlay").forEach(function(overlay) {
    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) overlay.style.display = "none";
    });
});


function openModalProfil()  { document.getElementById('modalProfil').style.display = 'flex'; }
function closeModalProfil() { document.getElementById('modalProfil').style.display = 'none'; }