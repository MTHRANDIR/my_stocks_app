function deleteNote(noteId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}

function deletePortfolio(portfolioId) {
  fetch("/delete-portfolio", {
    method: "POST",
    body: JSON.stringify({ portfolioId: portfolioId }),
  }).then((_res) => {
    window.location.href = "/create_portfolio";
  });
}