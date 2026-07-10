
function nmap(){
	fetch('/api/nmap_result')
	.then (response => response.json())
	.then(data => {
		data.forEach(scan =>{

			let nmap = document.getElementById(`nmap-${scan.scan_id}`);

			if (nmap){
				let p = document.createElement("p");
				p.textContent=`port: ${scan.scan_id}`;

				nmap.appendChild(p);

			}

		});
	});
}


nmap();
