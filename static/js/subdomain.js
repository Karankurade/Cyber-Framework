const search =
document.getElementById("search");


const statusFilter =
document.getElementById("statusFilter");


const lengthFilter =
document.getElementById("lengthFilter");



function filterTable(){

    let searchValue =
        search.value.toLowerCase();


    let statusValue =
        statusFilter.value;


    let lengthValue =
        lengthFilter.value;



    document.querySelectorAll(".endpoint-row")
    .forEach(row=>{


        let url =
            row.children[1]
            .innerText
            .toLowerCase();


        let rowStatus =
            row.dataset.status;


        let rowLength =
            parseInt(row.dataset.length);



        let visible = true;



        // Search
        if(searchValue && !url.includes(searchValue)){
            visible = false;
        }



        // Status
        if(statusValue != "all" &&
           rowStatus != statusValue){

            visible = false;
        }



        // Length
        if(lengthValue == "Min_value" && rowLength > 10000){

            visible = false;

        }

        if(lengthValue == "Max_value" && rowLength < 100000){

            visible = false;

        }



        row.style.display =
            visible ? "" : "none";


    });

}



search.addEventListener(
    "keyup",
    filterTable
);


statusFilter.addEventListener(
    "change",
    filterTable
);


lengthFilter.addEventListener(
    "change",
    filterTable
);