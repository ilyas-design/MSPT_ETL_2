import { downloadTextFile, toCsv } from '../utils/export';

function ExportButtons({ filenamePrefix, rows }) {
  const safe = Array.isArray(rows) ? rows : [];

  const onExportJson = () => {
    downloadTextFile(
      `${filenamePrefix}.json`,
      JSON.stringify(safe, null, 2),
      'application/json;charset=utf-8'
    );
  };

  const onExportCsv = () => {
    downloadTextFile(
      `${filenamePrefix}.csv`,
      toCsv(safe),
      'text/csv;charset=utf-8'
    );
  };

  return (
    <div className="export-actions" role="group" aria-label="Export">
      <button className="btn btn-secondary btn-sm" type="button" onClick={onExportCsv} disabled={safe.length === 0}>
        Export CSV
      </button>
      <button className="btn btn-secondary btn-sm" type="button" onClick={onExportJson} disabled={safe.length === 0}>
        Export JSON
      </button>
    </div>
  );
}

export default ExportButtons;

