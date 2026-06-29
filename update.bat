@echo off
title HappyFoodTime - Database Synchronizer
echo ============================================================
echo        HappyFoodTime: AUTOMATIC DATABASE SYNCHRONIZER
echo ============================================================
echo.
echo This script will automatically:
echo 1. Check and install required python modules (selenium, geopy).
echo 2. Scrape all 581 items from your Google Maps Shared List.
echo 3. Query Google Maps & ArcGIS for detailed addresses & coordinates.
echo 4. Update the live website's stores_data.js database in real-time.
echo.
echo Press any key to start synchronization...
pause > nul
echo.

python "%~dp0\update_database.py"

echo.
echo Synchronization completed successfully!
echo Press any key to exit...
pause > nul
