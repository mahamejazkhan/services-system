// --- Global Initialisation: Yeh function page load hone par chalta hai ---
document.addEventListener('DOMContentLoaded', function() {
    
    // Check karte hain ki user kis page par hai aur phir uski zaroori functionality chalate hain
    const currentPage = window.location.pathname.split('/').pop();
    
    // --- 1. LOGIN.HTML FUNCTIONALITY ---
    if (currentPage === 'login.html' || currentPage === 'index.html' || currentPage === '') {
        initializeLoginPage();
    } 
    
    // --- 2. LUNCH_KIOSK.HTML FUNCTIONALITY ---
    else if (currentPage === 'lunch_kiosk.html') {
        initializeLunchKioskPage();
    }
    
    // NOTE: client_management.html aur superadmin.html ki functionality (jaise modals/buttons)
    // agar zaroorat ho to yahan add ki jayegi. Abhi hum sirf login aur kiosk ko focus kar rahe hain.
});


// ==============================================================================
// 1. LOGIN PAGE LOGIC (login.html)
// ==============================================================================
function initializeLoginPage() {
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault(); 
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // --- Super Admin Login (Redirect to superadmin.html) ---
            if (username === 'superadmin' && password === 'Wopla@123') {
                alert('Login Successful! Redirecting to Super Admin Dashboard.'); 
                window.location.href = 'superadmin.html'; 
                
            } 
            // --- Client Admin Login (Redirect to client_management.html) ---
            else if (username === 'clientadmin' && password === 'Wopla@123') {
                alert('Login Successful! Redirecting to Client Management.'); 
                window.location.href = 'client_management.html'; 
            }
            // --- Error Message ---
            else {
                alert('Login Failed: Invalid Username or Password. Please try again.');
            }
        });
    }
}


// ==============================================================================
// 2. LUNCH KIOSK PAGE LOGIC (lunch_kiosk.html)
// ==============================================================================

// Global counter for new dishes
let dishIdCounter = 5; 

// Initialise Kiosk Page (Page load hone par chalta hai)
function initializeLunchKioskPage() {
    
    // Modal aur Form variables
    const modal = document.getElementById('addDishModal');
    const openBtn = document.getElementById('openAddDishModal');
    const closeBtn = modal ? modal.querySelector('.close-btn') : null;
    const form = document.getElementById('newDishForm');

    // --- Modal Logic ---
    if (openBtn && modal) {
        openBtn.addEventListener('click', () => { modal.style.display = "block"; });
    }
    if (closeBtn && form) {
        closeBtn.addEventListener('click', () => { modal.style.display = "none"; form.reset(); });
    }
    
    // Window click bahar
    window.addEventListener('click', (event) => { 
        if (modal && event.target === modal) { 
            modal.style.display = "none"; 
            if (form) form.reset(); 
        } 
    });

    // --- Add New Dish Submission ---
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const name = document.getElementById('newDishName').value;
            const count = parseInt(document.getElementById('initialCount').value); 
            
            if (name && !isNaN(count) && count >= 0) {
                addNewDish(name, count);
                modal.style.display = "none";
                form.reset();
            } else {
                alert("Error: Please enter a valid Dish Name and non-negative Count.");
            }
        });
    }
    
    // Page load hone par total count update karein
    updateTotalCount();
}

// --- Common Kiosk Functions (HTML se directly call hote hain) ---

// 1. Count Change
window.changeCount = function(dishId, change) {
    const row = document.querySelector(`tr[data-dish-id="${dishId}"]`);
    if (!row) return;

    const countDisplay = row.querySelector('.count-display');
    let currentCount = parseInt(countDisplay.getAttribute('data-count'));
    let newCount = Math.max(0, currentCount + change);

    countDisplay.setAttribute('data-count', newCount);
    countDisplay.textContent = newCount;
    
    updateTotalCount();
};

// 2. Update Total Count
function updateTotalCount() {
    const allCounts = document.querySelectorAll('#dishTableBody .count-display');
    let total = 0;
    allCounts.forEach(el => {
        total += parseInt(el.getAttribute('data-count'));
    });
    const totalDisplay = document.getElementById('totalDishesCount');
    if(totalDisplay) {
        totalDisplay.textContent = total;
    }
}

// 3. Add New Dish
function addNewDish(name, count) {
    const tbody = document.getElementById('dishTableBody');
    if (!tbody) return;
    
    const newId = dishIdCounter++;
    const newRow = document.createElement('tr');
    newRow.setAttribute('data-dish-id', newId);
    
    newRow.innerHTML = `
        <td>**${name}**</td>
        <td><span class="highlight-count count-display" data-count="${count}">${count}</span></td>
        <td>
            <div class="count-controls">
                <button onclick="changeCount(${newId}, -1)">-</button>
                <button onclick="changeCount(${newId}, 1)">+</button>
            </div>
        </td>
    `;
    
    const totalRow = tbody.querySelector('.total-row');
    tbody.insertBefore(newRow, totalRow);
    
    updateTotalCount();
}

// ==============================================================================
// 3. CLIENT_MANAGEMENT.HTML LOGIC
// ==============================================================================

// NOTE: Agar aap client_management.html ka modal (Create New Company) bhi isi JS file se handle karna chahti hain, 
// to uski initialization function yahan add kar dein.
function initializeClientManagementPage() {
    const modal = document.getElementById('addCompanyModal');
    const openBtn = document.getElementById('openAddCompanyModal');
    
    if (openBtn && modal) {
        // ... Client Management Modal/Form logic yahan aayega ...
    }
}