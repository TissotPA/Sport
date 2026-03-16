# Publie le fichier coach_planner.json sur la branche gh-pages
$date = Get-Date -Format "yyyy/MM/dd-HH:mm:ss"

git add coach_planner.json
git commit -m "Mise a jour donnees $date"
git push
git checkout gh-pages --force
Remove-Item -Recurse -Force static, templates, __pycache__ -ErrorAction SilentlyContinue
git checkout dev -- coach_planner.json
git add coach_planner.json
git commit -m "Mise a jour donnees $date"
git push
git checkout dev
