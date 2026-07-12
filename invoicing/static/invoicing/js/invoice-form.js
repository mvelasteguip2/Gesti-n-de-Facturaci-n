(function () {
  const api = new ApiClient();
  const svc = new InvoiceService(api);

  const els = {
    form: document.getElementById('invoiceForm'),
    productosBody: document.getElementById('detalleBody'),
    emptyDetalle: document.getElementById('emptyDetalle'),
    totalSubtotal: document.getElementById('totalSubtotal'),
    totalIva: document.getElementById('totalIva'),
    totalGeneral: document.getElementById('totalGeneral'),
    productosJson: document.getElementById('productosJson'),
    searchProducto: document.getElementById('searchProducto'),
    resultsProducto: document.getElementById('resultsProducto'),
  };

  let lines = [];

  function formatMoney(value) {
    return '$' + value.toFixed(2);
  }

  function actualizarTotales() {
    const totals = InvoiceCalculator.calcTotals(lines);
    if (els.totalSubtotal) els.totalSubtotal.textContent = formatMoney(totals.subtotal);
    if (els.totalIva) els.totalIva.textContent = formatMoney(totals.iva);
    if (els.totalGeneral) els.totalGeneral.textContent = formatMoney(totals.total);
    if (els.productosJson) {
      els.productosJson.value = JSON.stringify(
        lines.map((line) => ({
          producto_id: line.id,
          cantidad: line.cantidad,
          descuento_pct: line.descuentoPct,
        }))
      );
    }
    if (els.emptyDetalle) els.emptyDetalle.classList.toggle('d-none', lines.length > 0);
  }

  function recalcLine(line) {
    const calc = InvoiceCalculator.calcLine(line.cantidad, line.precio, line.descuentoPct, line.ivaPct);
    line.subtotal = calc.subtotal;
    line.ivaValor = calc.ivaValor;
    line.total = calc.total;
  }

  function renderLine(index) {
    const line = lines[index];
    recalcLine(line);

    const row = document.createElement('tr');
    row.dataset.index = String(index);
    row.innerHTML = `
      <td class="small">${line.codigo}</td>
      <td>${line.nombre}<div class="small text-muted">Stock: ${line.stockDisponible}</div></td>
      <td><input type="number" class="form-control form-control-sm qty" value="${line.cantidad}" min="1" max="${line.stockDisponible}" style="width:76px"></td>
      <td>${formatMoney(line.precio)}</td>
      <td><input type="number" class="form-control form-control-sm desc" value="${line.descuentoPct}" min="0" max="100" step="0.01" style="width:82px"></td>
      <td class="text-end">${formatMoney(line.subtotal)}</td>
      <td class="text-end">${formatMoney(line.ivaValor)}</td>
      <td class="text-end fw-semibold">${formatMoney(line.total)}</td>
      <td class="text-end"><button type="button" class="btn btn-sm btn-outline-danger remove-line"><i class="bi bi-x"></i></button></td>
    `;

    row.querySelector('.qty').addEventListener('change', function () {
      const value = parseInt(this.value, 10) || 0;
      lines[index].cantidad = value;
      this.classList.toggle('is-invalid', value <= 0 || value > line.stockDisponible);
      renderAllLines();
      actualizarTotales();
    });

    row.querySelector('.desc').addEventListener('change', function () {
      const value = parseFloat(this.value) || 0;
      lines[index].descuentoPct = Math.min(Math.max(value, 0), 100);
      renderAllLines();
      actualizarTotales();
    });

    row.querySelector('.remove-line').addEventListener('click', function () {
      lines.splice(index, 1);
      renderAllLines();
      actualizarTotales();
    });

    return row;
  }

  function renderAllLines() {
    if (!els.productosBody) return;
    els.productosBody.innerHTML = '';
    lines.forEach((_, index) => {
      els.productosBody.appendChild(renderLine(index));
    });
  }

  function addProduct(producto) {
    if (lines.some((line) => line.id === producto.id)) return;
    lines.push({
      id: producto.id,
      codigo: producto.codigo,
      nombre: producto.nombre,
      precio: parseFloat(producto.precio),
      ivaPct: parseFloat(producto.iva_porcentaje),
      stockDisponible: producto.stock,
      cantidad: 1,
      descuentoPct: 0,
      subtotal: 0,
      ivaValor: 0,
      total: 0,
    });
    renderAllLines();
    actualizarTotales();
    if (els.resultsProducto) els.resultsProducto.innerHTML = '';
    if (els.searchProducto) els.searchProducto.value = '';
  }

  function renderProductResults(data) {
    if (!els.resultsProducto) return;
    if (!data.length) {
      els.resultsProducto.innerHTML = '<div class="list-group-item text-muted small">Sin resultados.</div>';
      return;
    }
    els.resultsProducto.innerHTML = data.map((producto) => `
      <a href="#" class="list-group-item list-group-item-action" data-id="${producto.id}">
        <strong>${producto.codigo}</strong> - ${producto.nombre}
        <span class="float-end">${formatMoney(parseFloat(producto.precio))} | Stock: ${producto.stock}</span>
      </a>
    `).join('');
    els.resultsProducto.querySelectorAll('a').forEach((item) => {
      item.addEventListener('click', function (event) {
        event.preventDefault();
        const producto = data.find((entry) => String(entry.id) === this.dataset.id);
        if (producto) addProduct(producto);
      });
    });
  }

  if (els.searchProducto) {
    let timeout;
    els.searchProducto.addEventListener('input', function () {
      clearTimeout(timeout);
      const q = this.value.trim();
      if (q.length < 2) {
        if (els.resultsProducto) els.resultsProducto.innerHTML = '';
        return;
      }
      timeout = setTimeout(async () => {
        try {
          const data = await svc.buscarProductos(q);
          renderProductResults(data);
        } catch (error) {
          if (els.resultsProducto) {
            els.resultsProducto.innerHTML = `<div class="list-group-item text-danger small">${error.message}</div>`;
          }
        }
      }, 300);
    });
  }

  if (els.form) {
    els.form.addEventListener('submit', function (event) {
      if (!lines.length) {
        event.preventDefault();
        alert('Debe agregar al menos un producto.');
        return;
      }
      const invalid = lines.some((line) => line.cantidad <= 0 || line.cantidad > line.stockDisponible);
      if (invalid) {
        event.preventDefault();
        alert('Revise las cantidades ingresadas.');
      }
    });
  }

  if (els.productosBody) actualizarTotales();
})();
