const API_BASE = "http://127.0.0.1:5000";  // Flask Backend

// ✅ Fetch Cities on Page Load
window.onload = () => {
    fetch(`${API_BASE}/cities`)
        .then(res => res.json())
        .then(data => {
            const citySelect = document.getElementById("citySelect");
            data.forEach(city => {
                const option = document.createElement("option");
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        });
};

// ✅ Form Submission (Add Tree)
document.getElementById("addTreeForm").addEventListener("submit", function(event) {
    event.preventDefault();

    // Collecting Form Data (with correct input types)
    const treeData = {
        custom_id: document.getElementById("custom_id").value.trim(),
        city: document.getElementById("city").value.trim(),
        address: document.getElementById("address").value.trim(),
        latitude: parseFloat(document.getElementById("latitude").value) || null,
        longitude: parseFloat(document.getElementById("longitude").value) || null,
        species: document.getElementById("species").value.trim(),
        condition: document.getElementById("condition").value.trim(),
        comments: document.getElementById("comments").value.trim(),

        // ✅ New fields (parse correct types)
        height: document.getElementById("height").value.trim(),          // String (e.g., "M")
        trunk_diameter_cm: parseFloat(document.getElementById("trunk_diameter_cm").value) || null,  // Float (e.g., 45.0)
        crown_diameter_m: parseFloat(document.getElementById("crown_diameter_m").value) || null,    // Float (e.g., 8.5)
        actions: document.getElementById("actions").value.trim(),        // String (e.g., "Pruned")
        age: document.getElementById("age").value.trim(),                // String (e.g., "Young")
        location: document.getElementById("location").value.trim(),      // String (e.g., "Near park")
        cpc: document.getElementById("cpc").value.trim(),                // String (e.g., "A1")

        // Handle date properly
        next_check: document.getElementById("next_check").value || null  // Date (e.g., "2025-12-01")
    };

    // ✅ Input Validation
    if (!treeData.custom_id || !treeData.city || !treeData.species || !treeData.condition) {
        alert("Custom ID, City, Species, and Condition are required.");
        return;
    }

    // ✅ Send the request to add the tree
    fetch(`${API_BASE}/add_tree`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(treeData)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("status").innerText = data.message;
        fetchTrees(); // Refresh tree list
    })
    .catch(error => console.error("Error:", error));
});

// 📍 Get GPS Location and autofill latitude/longitude
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            document.getElementById("latitude").value = position.coords.latitude;
            document.getElementById("longitude").value = position.coords.longitude;
        }, function(error) {
            document.getElementById("status").innerText = "Error getting location: " + error.message;
        });
    } else {
        document.getElementById("status").innerText = "Geolocation is not supported by this browser.";
    }
}

// Fetch Streets based on selected city
function fetchStreets() {
    let city = document.getElementById("citySelect").value;
    if (!city) return;

    fetch(`${API_BASE}/streets/${city}`)
        .then(res => res.json())
        .then(data => {
            let streetSelect = document.getElementById("streetSelect");
            streetSelect.innerHTML = `<option value="">-- Choose a street --</option>`;
            data.forEach(street => {
                let option = document.createElement("option");
                option.value = street;
                option.textContent = street;
                streetSelect.appendChild(option);
            });
        });
}

// ✅ Fetch Trees with Filters
function fetchTrees() {
    const city = document.getElementById("citySelect").value;
    const addressPart = document.getElementById("streetSearch").value.trim();

    let url = `${API_BASE}/trees?city=${city}`;
    if (addressPart) url += `&address=${encodeURIComponent(addressPart)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            const tableBody = document.getElementById("treeList");
            tableBody.innerHTML = "";
            data.forEach(tree => {
                const row = `
                    <tr>
                        <td>${tree.id}</td>
                        <td>${tree.custom_id}</td>
                        <td>${tree.species}</td>
                        <td>${tree.condition}</td>
                        <td>${tree.address}</td>
                        <td>
                            <button class="btn btn-warning btn-sm" onclick="editTree(${tree.id}, '${tree.condition}', '${tree.comments}')">Edit</button>
                        </td>
                        <td>
                            <button class="btn btn-primary btn-sm" onclick="viewTreeDetails(${tree.id})">View Details</button>
                        </td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteTreeById(${tree.id})">Delete</button>
                        </td>
                    </tr>`;
                tableBody.innerHTML += row;
            });
        });
}


function showComments(comments) {
    alert(`Tree Comments:\n${comments}`);
}

function fetchTreeById() {
    let customId = document.getElementById("treeIdInput").value;
    if (!customId) return alert("Please enter a Custom ID");

    fetch(`${API_BASE}/tree/custom/${customId}`)
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                alert("Tree not found!");
                return;
            }
            alert(`Tree Found:\nSpecies: ${data.species}\nCondition: ${data.condition}\nComments: ${data.comments}`);
        })
        .catch(() => alert("Tree not found"));
}


function editTree(treeId, currentCondition, currentComments) {
    // Collect new values with prompts (or a better UI could be built)
    const newCondition = prompt("Enter new condition:", currentCondition);
    const newComments = prompt("Enter new comments:", currentComments);
    const newActions = prompt("Actions Taken:");
    const newHeight = prompt("Height (e.g., M):");
    const newTrunkDiameter = prompt("Trunk Diameter (cm):");
    const newCrownDiameter = prompt("Crown Diameter (m):");
    const newAge = prompt("Age (e.g., Young, Old):");
    const newLocation = prompt("Location Notes:");
    const newCPC = prompt("CPC Code:");
    const newNextCheck = prompt("Next Check Date (YYYY-MM-DD):");

    if (newCondition === null || newComments === null) {
        alert("Update canceled.");
        return;
    }

    const updatedData = {
        condition: newCondition.trim(),
        comments: newComments.trim(),
        actions: newActions ? newActions.trim() : "",
        height: newHeight ? newHeight.trim() : "",
        trunk_diameter_cm: newTrunkDiameter ? parseFloat(newTrunkDiameter) : null,
        crown_diameter_m: newCrownDiameter ? parseFloat(newCrownDiameter) : null,
        age: newAge ? newAge.trim() : "",
        location: newLocation ? newLocation.trim() : "",
        cpc: newCPC ? newCPC.trim() : "",
        next_check: newNextCheck ? newNextCheck.trim() : null,
    };

    // Send PATCH request to update the tree
    fetch(`${API_BASE}/tree/${treeId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);  // Show success message
        fetchTrees();         // Refresh the tree list
    })
    .catch(error => console.error("Error updating tree:", error));
}


function viewTreeDetails(treeId) {
    fetch(`${API_BASE}/tree/${treeId}`)
        .then(res => res.json())
        .then(tree => {
            alert(`
Tree Details:
Species: ${tree.species}
Condition: ${tree.condition}
Height: ${tree.height}
Trunk Diameter: ${tree.trunk_diameter_cm} cm
Crown Diameter: ${tree.crown_diameter_m} m
Age: ${tree.age}
Actions: ${tree.actions}
Location: ${tree.location}
CPC: ${tree.cpc}
Next Check: ${tree.next_check}
Comments: ${tree.comments}
            `);
        })
        .catch(() => alert("Tree not found"));
}

// ✅ Delete Tree by ID
function deleteTreeById(treeId) {
    if (!confirm("Are you sure you want to delete this tree?")) return;

    fetch(`${API_BASE}/tree/custom/${treeId}`, { method: "DELETE" })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            fetchTrees();
        })
        .catch(error => console.error("Error deleting tree:", error));
}



let map;
let markers = [];

// Toggle map visibility and load markers
function toggleMap() {
    let mapDiv = document.getElementById("map");
    if (mapDiv.style.display === "none") {
        mapDiv.style.display = "block";

        // Initialize map only once
        if (!map) {
            map = L.map("map").setView([45.07, 7.69], 13);  // Default: Torino
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
        }

        fetchTreesOnMap();
    } else {
        mapDiv.style.display = "none";
    }
}

// Display trees on the map
function fetchTreesOnMap() {
    let city = document.getElementById("citySelect").value;
    let addressPart = document.getElementById("streetSearch").value.trim();

    let url = `${API_BASE}/trees?city=${encodeURIComponent(city)}`;
    if (addressPart) url += `&address=${encodeURIComponent(addressPart)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            // Clear old markers
            if (markers) {
                markers.forEach(marker => map.removeLayer(marker));
                markers = [];
            }

            if (data.length === 0) {
                alert("No trees found for the selected filters.");
                return;
            }

            // Add markers for all valid trees
            data.forEach(tree => {
                if (!tree.latitude || !tree.longitude) {
                    console.warn(`Skipping tree ${tree.custom_id} due to missing coordinates.`);
                    return;  // Skip trees with missing coordinates
                }

                // Create a marker for each tree
                let marker = L.marker([tree.latitude, tree.longitude])
                    .bindPopup(`
                        <b>Species:</b> ${tree.species}<br>
                        <b>Condition:</b> ${tree.condition}<br>
                        <b>Address:</b> ${tree.address}<br>
                        <b>Next Check:</b> ${tree.next_check || "N/A"}
                    `);
                marker.addTo(map);
                markers.push(marker);
            });

            // Center map on the first tree found
            const firstTree = data[0];
            if (firstTree && firstTree.latitude && firstTree.longitude) {
                map.setView([firstTree.latitude, firstTree.longitude], 15);
            }
        })
        .catch(error => console.error("Error fetching trees for map:", error));
}


