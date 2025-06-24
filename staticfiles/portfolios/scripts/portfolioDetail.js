const netBalanceCard = document.querySelector("#net-balance-card");
const netBalanceCardToggle = document.querySelector("#net-balance-card-toggle");


netBalanceCardToggle.onclick = function(e) {
    const toggleText = this.dataset.toggletext;
    const newToggleText = this.innerHTML;

    netBalanceCard.classList.toggle("show-block");
    netBalanceCardToggle.innerHTML = toggleText;
    netBalanceCardToggle.dataset.toggletext = newToggleText;
}


