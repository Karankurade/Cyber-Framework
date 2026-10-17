function updateProgressBar() {

    fetch('/api/scans')
        .then(response => response.json())
        .then(data => {

            data.forEach(scan => {

                let progressBar =
                    document.getElementById(
                        `scanProgress-${scan.id}`
                    );

                let text =
                    document.getElementById(
                        `progressText-${scan.id}`
                    );

                let statusText =
                    document.getElementById(
                        `scanStatus-${scan.id}`
                    );

                let button =
                    document.getElementById(
                        `scan-button-${scan.id}`
                    );

                let timerElement =
                    document.getElementById(
                        `elapsedTime-${scan.id}`
                    );
		let current_status = 
			    document.getElementById(`statusText-${scan.id}`
			    );

                if (timerElement) {

                    const mins =
                        Math.floor(scan.elapsed / 60);

                    const secs =
                        scan.elapsed % 60;

                    timerElement.textContent =
                        `${String(mins).padStart(2, '0')}:` +
                        `${String(secs).padStart(2, '0')}`;
                }

                if (progressBar) {

                    progressBar.style.width =
                        scan.progress + "%";

                    text.textContent =
                        scan.progress + "%";
                }

                if (statusText) {
                    statusText.textContent =
                        scan.scan_status;
                }

		if (current_status) {
			current_status.textContent = 
				scan.scan_status;
		}

                if (button) {

                    if (scan.progress < 100) {
                        button.style.display = "block";
                    } else {
                        button.style.display = "none";
                    }
                }

            });

        })
        .catch(error => {
            console.error(
                "Error fetching scan data:",
                error
            );
        });
}

// Run immediately when page loads
updateProgressBar();

// Refresh every second
setInterval(updateProgressBar, 1000);
