function initBoard() {
    //document.getElementById("r1c3").firstChild.focus();
    //console.log("initBoard() called!");
  }

function newGame() {
    let table = document.getElementById("t1");
    let inputs = table.getElementsByTagName("input");
    for (let i=0; i < inputs.length; i++) {
            if (!inputs[i].disabled) {
                    inputs[i].value = "";
                  }
          }
    initBoard();
  }

function checkCellValid(cell) {
    let number = parseInt(cell.value);
    let isValid = (Number.isInteger(number) && number >= 1 && number <=9);
    if (isValid) {
            cell.style.color = "green";
            cell.blur();
          }
    else
      cell.value = "";
  }

function makeMove() {
    table_cell = document.getElementById("id_location").value;
    number = document.getElementById("id_number").value;
    document.getElementById(table_cell).innerHTML = "<input type='text' value='" + number + "' style='color:green'/>";
    document.getElementById("id_location").value = "";
    document.getElementById("id_number").value = "";
    return false;
  }