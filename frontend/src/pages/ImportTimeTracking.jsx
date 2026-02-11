import { useState } from 'react';
import { Upload, Download, AlertCircle, CheckCircle, FileText, X } from 'lucide-react';
import api from '../services/api';

const ImportTimeTracking = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [showErrors, setShowErrors] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setResults(null);
    } else {
      alert('Por favor selecciona un archivo CSV');
      e.target.value = '';
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Por favor selecciona un archivo CSV');
      return;
    }

    setUploading(true);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/csv-import/time-tracking', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.results);
      
      if (response.data.results.imported > 0) {
        alert(`✅ Importación exitosa: ${response.data.results.imported} registros importados`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error al importar el archivo: ' + (error.response?.data?.error || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/csv-import/template', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'plantilla_importacion.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading template:', error);
      alert('Error al descargar la plantilla');
    }
  };

  const handleReset = () => {
    setFile(null);
    setResults(null);
    setShowErrors(false);
    document.getElementById('file-input').value = '';
  };

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          Importar Registros de Horas
        </h1>
        <p className="text-gray-600">
          Importa registros de horas trabajadas desde un archivo CSV
        </p>
      </div>

      {/* Instrucciones */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Formato del archivo CSV
        </h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>El archivo debe tener las siguientes columnas:</p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li><strong>fecha</strong>: Formato DD/MM/YYYY (ej: 5/1/2026)</li>
            <li><strong>entrada</strong>: Hora de entrada en formato HH:MM (ej: 16:00)</li>
            <li><strong>salida</strong>: Hora de salida en formato HH:MM (ej: 21:15)</li>
            <li><strong>mail</strong>: Email del empleado (ej: maria.gonzalez@galia.com)</li>
          </ul>
          <p className="mt-3">
            <strong>Ejemplo:</strong>
          </p>
          <pre className="bg-white p-2 rounded border border-blue-300 text-xs overflow-x-auto">
fecha,entrada,salida,mail{'\n'}
5/1/2026,16:00,21:15,maria.gonzalez@galia.com{'\n'}
10/1/2026,17:00,21:00,maria.gonzalez@galia.com
          </pre>
        </div>
      </div>

      {/* Descargar plantilla */}
      <div className="bg-white rounded-lg shadow mb-6 p-4 md:p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Plantilla CSV</h2>
        <p className="text-gray-600 mb-4">
          Descarga una plantilla de ejemplo para ver el formato correcto
        </p>
        <button
          onClick={handleDownloadTemplate}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          <Download className="w-4 h-4" />
          Descargar Plantilla
        </button>
      </div>

      {/* Upload */}
      <div className="bg-white rounded-lg shadow mb-6 p-4 md:p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Subir Archivo</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seleccionar archivo CSV
            </label>
            <input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                cursor-pointer"
            />
          </div>

          {file && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FileText className="w-4 h-4" />
              <span>{file.name}</span>
              <span className="text-gray-400">({(file.size / 1024).toFixed(2)} KB)</span>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <Upload className="w-4 h-4" />
              {uploading ? 'Importando...' : 'Importar'}
            </button>

            {file && (
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                <X className="w-4 h-4" />
                Cancelar
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Resultados */}
      {results && (
        <div className="bg-white rounded-lg shadow p-4 md:p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Resultados de la Importación</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-blue-600 mb-1">Total de filas</div>
              <div className="text-2xl font-bold text-blue-900">{results.total_rows}</div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-green-600 mb-1 flex items-center gap-1">
                <CheckCircle className="w-4 h-4" />
                Importados
              </div>
              <div className="text-2xl font-bold text-green-900">{results.imported}</div>
            </div>

            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-red-600 mb-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                Con errores
              </div>
              <div className="text-2xl font-bold text-red-900">{results.errors.length}</div>
            </div>
          </div>

          {/* Errores */}
          {results.errors.length > 0 && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  Registros con errores ({results.errors.length})
                </h3>
                <button
                  onClick={() => setShowErrors(!showErrors)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {showErrors ? 'Ocultar' : 'Mostrar'} detalles
                </button>
              </div>

              {showErrors && (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {results.errors.map((error, idx) => (
                    <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div className="flex items-start gap-2 mb-2">
                        <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="font-semibold text-red-900 text-sm">
                            Fila {error.row}
                          </div>
                          <div className="text-xs text-red-700 mt-1">
                            {error.data.fecha && <span className="mr-2">📅 {error.data.fecha}</span>}
                            {error.data.entrada && <span className="mr-2">⏰ {error.data.entrada}</span>}
                            {error.data.salida && <span className="mr-2">⏰ {error.data.salida}</span>}
                            {error.data.mail && <span>✉️ {error.data.mail}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="ml-6 space-y-1">
                        {error.errors.map((err, errIdx) => (
                          <div key={errIdx} className="text-sm text-red-800">
                            • {err}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  💡 <strong>Tip:</strong> Corrige los errores en el archivo CSV y vuelve a importar. 
                  Los registros ya importados no se duplicarán.
                </p>
              </div>
            </div>
          )}

          {results.imported > 0 && results.errors.length === 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-800">
                <CheckCircle className="w-5 h-5" />
                <p className="font-semibold">
                  ¡Importación completada exitosamente!
                </p>
              </div>
              <p className="text-sm text-green-700 mt-1">
                Todos los registros se importaron correctamente. Puedes verificarlos en el módulo de Sueldos.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Validaciones */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-6">
        <h3 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Validaciones automáticas
        </h3>
        <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
          <li>Se verifica que el email del empleado exista en la base de datos</li>
          <li>Se valida que la hora de entrada sea anterior a la hora de salida</li>
          <li><strong>No se permiten bloques de trabajo superpuestos</strong> para el mismo empleado en el mismo día</li>
          <li>Se detectan y reportan formatos de fecha/hora inválidos</li>
        </ul>
      </div>
    </div>
  );
};

export default ImportTimeTracking;
