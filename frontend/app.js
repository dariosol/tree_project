const API_BASE = "http://127.0.0.1:5000";  // Flask Backend

// Fetch Cities on Page Load
window.onload = () => {
    fetch(`${API_BASE}/cities`)
        .then(res => res.json())
        .then(data => {
            let citySelect = document.getElementById("citySelect");
            data.forEach(city => {
                let option = document.createElement("option");
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        });
};



document.getElementById("addTreeForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let treeData = {
        custom_id: document.getElementById("custom_id").value,
        city: document.getElementById("city").value,
        address: document.getElementById("address").value,
        latitude: document.getElementById("latitude").value,
        longitude: document.getElementById("longitude").value,
        species: document.getElementById("species").value,
        condition: document.getElementById("condition").value,
        comments: document.getElementById("comments").value
    };

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

function fetchTrees() {
    let city = document.getElementById("citySelect").value;
    let addressPart = document.getElementById("streetSearch").value;  // Get input value

    let url = `${API_BASE}/trees?city=${city}`;
    if (addressPart) url += `&address=${encodeURIComponent(addressPart)}`;  // Send as query param

    fetch(url)
        .then(res => res.json())
        .then(data => {
            let tableBody = document.getElementById("treeList");
            tableBody.innerHTML = "";
            data.forEach(tree => {
                let row = `<tr>
                    <td>${tree.id}</td>
                    <td>${tree.custom_id}</td>
                    <td>${tree.species}</td>
                    <td>${tree.condition}</td>
                    <td>${tree.address}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editTree(${tree.id}, '${tree.condition}', '${tree.comments}')">Edit</button>
                    </td>
                </tr>`;
                tableBody.innerHTML += row;
            });
        });
}
function editTree(treeId, currentCondition, currentComments) {
    let newCondition = prompt("Enter new condition:", currentCondition);
    let newComments = prompt("Enter new comments:", currentComments);

    if (newCondition === null || newComments === null) {
        alert("Update canceled.");
        return;
    }

    let updatedData = {
        condition: newCondition,
        comments: newComments
    };

    fetch(`${API_BASE}/tree/${treeId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);  // Show success message
        fetchTrees();  // Refresh the tree list
    })
    .catch(error => console.error("Error updating tree:", error));
}


// Fetch Tree by Custom ID
function fetchTreeById() {
    let treeId = document.getElementById("treeIdInput").value;
    if (!treeId) return alert("Enter a Tree ID");

    fetch(`${API_BASE}/tree/custom/${treeId}`)
        .then(res => res.json())
        .then(data => {
            alert(`Tree Found: ${data.species} at ${data.address}`);
        })
        .catch(() => alert("Tree not found"));
}

function deleteTreeById(treeId) {
    if (!treeId) return alert("Invalid Tree ID");

    if (!confirm("Are you sure you want to delete this tree?")) {
        return;
    }

    fetch(`${API_BASE}/tree/${treeId}`, { method: "DELETE" })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            fetchTrees();  // ✅ Refresh tree list
        })
        .catch(error => console.error("Error deleting tree:", error));
}


function showComments(comments) {
    alert(`Tree Comments:\n${comments}`);
}

// Show Trees on Map
let map, markers = [];
function toggleMap() {
    let mapDiv = document.getElementById("map");
    if (mapDiv.style.display === "none") {
        mapDiv.style.display = "block";
        if (!map) {
            map = L.map("map").setView([45.07, 7.69], 13); // Default: Torino
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
        }
        fetchTreesOnMap();
    } else {
        mapDiv.style.display = "none";
    }
}

function fetchTreesOnMap() {
    let city = document.getElementById("citySelect").value;
    let addressPart = document.getElementById("streetSearch").value;

    let url = `${API_BASE}/trees?city=${city}`;
    if (addressPart) url += `&address=${encodeURIComponent(addressPart)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            // Clear old markers
            markers.forEach(m => map.removeLayer(m));
            markers = [];

            if (data.length === 0) {
                alert("No trees found for the selected filters.");
                return;
            }

            // Add new markers for each tree
            data.forEach(tree => {
                if (!tree.latitude || !tree.longitude) {
                    console.warn(`Skipping tree ${tree.custom_id} due to missing coordinates.`);
                    return;  // Skip trees without coordinates
                }

                let marker = L.marker([tree.latitude, tree.longitude])
                    .bindPopup(`<b>${tree.species}</b><br>${tree.address}`);
                marker.addTo(map);
                markers.push(marker);
            });

            // Recenter map on first tree
            let firstTree = data[0];
            if (firstTree.latitude && firstTree.longitude) {
                map.setView([firstTree.latitude, firstTree.longitude], 15);
            }
        })
        .catch(error => console.error("Error fetching trees for map:", error));
}
