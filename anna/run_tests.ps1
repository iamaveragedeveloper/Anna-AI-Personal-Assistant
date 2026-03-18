# Anna Test Runner (PowerShell)

echo "🧪 Running Anna Test Suite"
echo "=========================="
echo ""

# Check Ollama is running
echo "Checking Ollama..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
    echo "✅ Ollama is running"
} catch {
    echo "❌ Ollama is not running!"
    echo "   Start it with: ollama serve"
    exit 1
}
echo ""

# Run tests
echo "Running tests..."
$env:PYTHONUTF8=1
$env:PYTHONPATH="."
& ".\venv\Scripts\pytest.exe" tests/ -v --tb=short

# Check exit code
if ($LASTEXITCODE -eq 0) {
    echo ""
    echo "✅ All tests passed!"
} else {
    echo ""
    echo "❌ Some tests failed"
    exit 1
}
