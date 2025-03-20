# PowerShell script to find missing type hints & UML connections in cruise_finder

# Define the project path
$ProjectPath = "./src"

Write-Host "Checking for missing type hints and references in: $ProjectPath" -ForegroundColor Cyan

# 1. Find class attributes without type hints
Write-Host "
[1] Finding class attributes without type hints..." -ForegroundColor Yellow
Select-String -Path "$ProjectPath/*.py" -Pattern "self\.\w+\s*=" | ForEach-Object { $_.Line }

# 2. Find methods missing return type hints
Write-Host "
[2] Finding methods missing return type hints..." -ForegroundColor Yellow
Select-String -Path "$ProjectPath/*.py" -Pattern "def .*[^)]:" | Where-Object { $_ -notmatch "->" } | ForEach-Object { $_.Line }

# 3. Find classes without obvious associations (missing self-references)
Write-Host "
[3] Finding classes missing references to other classes..." -ForegroundColor Yellow
Select-String -Path "$ProjectPath/*.py" -Pattern "class \w+" | ForEach-Object { $_.Line }
Select-String -Path "$ProjectPath/*.py" -Pattern "self\.\w+:?" | ForEach-Object { $_.Line }

# 4. Run mypy for deeper type hint checking
Write-Host "
[4] Running mypy for type checking..." -ForegroundColor Yellow
mypy --disallow-untyped-defs --disallow-untyped-calls "$ProjectPath" --ignore-missing-imports

# 5. (Optional) Generate UML diagram using pyreverse
if (Get-Command pyreverse -ErrorAction SilentlyContinue) {
    Write-Host "
[5] Generating UML diagram..." -ForegroundColor Yellow
    pyreverse -o png -p cruise_finder "$ProjectPath"
    Write-Host "UML Diagram saved as classes.png" -ForegroundColor Green
} else {
    Write-Host "
[5] Skipping UML generation - install pylint to enable" -ForegroundColor Red
}

Write-Host "
Check complete!" -ForegroundColor Green
