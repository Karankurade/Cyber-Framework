function UpdateHistory() {
    fetch('/api/scans')
        .then(response => response.json())
        .then(data => {

            data.forEach(scan => {

                let targetStatus =
                    document.getElementById(`status-${scan.id}`);

                if (targetStatus){
			targetStatus.textContent = scan.scan_status;
			
			targetStatus.classList.remove(
				"starting",
                "Running",
                "Completed"
			);
			targetStatus.classList.add(scan.scan_status);
		}

                document.getElementById(`time-${scan.id}`).textContent =
                    minutesAgo(scan.time);

            });

        });
}

function minutesAgo(timeString){

    const start = new Date(timeString);
    const now = new Date();

    const diff  = now - start;

    const seconds = Math.floor(diff / 1000);

    if (seconds < 60){
        return seconds + " sec ago";
    }

    const minutes = Math.floor(seconds / 60);

    if (minutes < 60){
        return minutes + " min ago";
    }

    const hours = Math.floor(minutes / 60);

    if (hours < 24){
        return hours + " hr ago";
    }

    const days = Math.floor(hours / 24);

    if (days < 7){
        return days + " day ago";
    }

    const weeks = Math.floor(days / 7);

    if (weeks < 4){
        return weeks + " week ago";
    }

    const months = Math.floor(days / 30);

    if (months < 12){
        return months + " month ago";
    }

    const years = Math.floor(days / 365);

    return years + " year ago";
}

setInterval(UpdateHistory, 1000);

setInterval(() =>{
	location.reload();
},20000)
