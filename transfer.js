let accountBalance = 1000;

function validateTransfer() {
    let fromAccount = document.getElementById("from-account").value;
    let toAccount = document.getElementById("to-account").value;
    let amount = parseFloat(document.getElementById("amount").value);
    let errorMessage = document.getElementById("error-message");

    errorMessage.textContent = '';

    if (!fromAccount || !toAccount || isNaN(amount) || amount <= 0) {
        errorMessage.textContent = 'Please enter valid account details and amount.';
    } else if (amount > accountBalance) {
        errorMessage.textContent = 'Insufficient balance for this transfer.';
    } else {
        accountBalance -= amount;
        alert('Transfer successful!');
    }
}
