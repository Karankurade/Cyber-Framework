function Scan_history(){
	fetch('/api/scans')
	  .then( response => response.json())
	  .then(data => {
		  data.forEach(scan =>{

			  let status_history =document.getElementById(`status-${scan.id}`);

			  let status_history1 = document.getElementById(`status1-${scan.id}`);

			  if (status_history1){

				status_history1.textContent = scan.scan_status;

				status_history1.classList.remove(
					"starting",
					"Running",
					"completed"
				);

				status_history1.classList.add(scan.scan_status)
			  }

			  if (status_history){
				  status_history.textContent = scan.scan_status;
			  }
		  });
	  });
}
setInterval(Scan_history,1000);

setInterval(() =>{
	locaton.reload()
},3000);

