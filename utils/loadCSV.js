export function loadCSVToLocalStorage(csvText) {
  const rows = csvText.trim().split("\n");
  const headers = rows[0].split(",");

  const data = rows.slice(1).map(row => {
    const values = row.split(",");
    let obj = {};

    headers.forEach((h, i) => {
      obj[h] = values[i];
    });

    return {
      date: obj.date,
      total: Number(obj.total),
      items: Array(Number(obj.items)).fill({ name: "Item" })
    };
  });

  localStorage.setItem("orders", JSON.stringify(data));
  console.log("CSV loaded into localStorage:", data);
}