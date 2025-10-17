# GiddyUp Documentation

**Complete documentation for the GiddyUp horse racing data platform**

Last Updated: October 16, 2025

---

## 📚 Core Documentation (Read These!)

### Getting Started
- **[00. Start Here](00_START_HERE.md)** - Overview, architecture, quick start
- **[01. Developer Guide](01_DEVELOPER_GUIDE.md)** - Complete backend development guide
- **[02. API Documentation](02_API_DOCUMENTATION.md)** - Full API reference with examples

### Database & Frontend
- **[03. Database Guide](03_DATABASE_GUIDE.md)** - Schema, queries, optimization
- **[04. Frontend Guide](04_FRONTEND_GUIDE.md)** - UI integration patterns

### Deployment & Operations
- **[05. Deployment Guide](05_DEPLOYMENT_GUIDE.md)** - Production deployment
- **[10. Troubleshooting](10_TROUBLESHOOTING.md)** - Common issues & solutions

---

## 🔧 Feature-Specific Guides

### Data Sources & Integration
- **[06. Sporting Life API](06_SPORTING_LIFE_API.md)** - Primary data source integration
- **[08. Live Prices](08_LIVE_PRICES.md)** - Betfair live price integration
- **[09. Auto-Update](09_AUTO_UPDATE.md)** - Automatic data updates

### Recent Fixes
- **[07. Course Fix Complete](07_COURSE_FIX_COMPLETE.md)** - Major Oct 16 fix (127k races)

---

## 🎯 Quick Links by Role

### 👨‍💻 I'm a Backend Developer

**Start here:**
1. [00_START_HERE.md](00_START_HERE.md) - 5 minutes
2. [01_DEVELOPER_GUIDE.md](01_DEVELOPER_GUIDE.md) - 30 minutes
3. [03_DATABASE_GUIDE.md](03_DATABASE_GUIDE.md) - Reference

**You'll learn:**
- Project structure & architecture
- How to add new endpoints
- Database schema & queries
- Testing & debugging

---

### 🎨 I'm a Frontend Developer

**Start here:**
1. [00_START_HERE.md](00_START_HERE.md) - 5 minutes
2. [04_FRONTEND_GUIDE.md](04_FRONTEND_GUIDE.md) - 20 minutes
3. [02_API_DOCUMENTATION.md](02_API_DOCUMENTATION.md) - Reference

**You'll learn:**
- API endpoints & responses
- TypeScript type definitions
- Common UI patterns
- Live price integration

---

### 🚀 I'm a DevOps Engineer

**Start here:**
1. [00_START_HERE.md](00_START_HERE.md) - 5 minutes
2. [05_DEPLOYMENT_GUIDE.md](05_DEPLOYMENT_GUIDE.md) - 30 minutes
3. [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md) - Reference

**You'll learn:**
- Production deployment
- Environment configuration
- Monitoring & logging
- Backup/restore procedures

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Start database
cd postgres && docker-compose up -d

# 2. Restore data
cat db_backup.sql | docker exec -i horse_racing psql -U postgres -d horse_db

# 3. Start API
cd backend-api
source ../settings.env
./bin/api

# 4. Test
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/races/today | jq
```

**Done!** API is running on http://localhost:8000

---

## 📖 Documentation Structure

```
docs/
├── 00_START_HERE.md           ⭐ Overview & architecture
├── 01_DEVELOPER_GUIDE.md      🛠️  Backend development
├── 02_API_DOCUMENTATION.md    📡 API reference
├── 03_DATABASE_GUIDE.md       🗄️  Database schema
├── 04_FRONTEND_GUIDE.md       🎨 UI integration
├── 05_DEPLOYMENT_GUIDE.md     🚀 Production deploy
├── 06_SPORTING_LIFE_API.md    📥 Data source
├── 07_COURSE_FIX_COMPLETE.md  ✅ Major fix (Oct 16)
├── 08_LIVE_PRICES.md          💹 Betfair prices
├── 09_AUTO_UPDATE.md          🔄 Auto-updates
├── 10_TROUBLESHOOTING.md      🐛 Common issues
├── features/                  📁 Feature docs
│   ├── AUTO_UPDATE_EXAMPLE_LOGS.md
│   └── (historical features)
└── archive/                   📦 Historical docs
    └── (76 archived files)
```

---

## 📊 Documentation Status

| Document | Status | Last Updated | Audience |
|----------|--------|--------------|----------|
| 00_START_HERE | ✅ Current | Oct 16, 2025 | All |
| 01_DEVELOPER_GUIDE | ✅ Current | Oct 15, 2025 | Backend |
| 02_API_DOCUMENTATION | ✅ Current | Oct 15, 2025 | All Devs |
| 03_DATABASE_GUIDE | ✅ Current | Oct 15, 2025 | Backend/Data |
| 04_FRONTEND_GUIDE | ✅ Current | Oct 15, 2025 | Frontend |
| 05_DEPLOYMENT_GUIDE | ✅ Current | Oct 15, 2025 | DevOps |
| 06_SPORTING_LIFE_API | ✅ Current | Oct 16, 2025 | Backend |
| 07_COURSE_FIX_COMPLETE | ✅ Current | Oct 16, 2025 | All |
| 08_LIVE_PRICES | ✅ Current | Oct 16, 2025 | All Devs |
| 09_AUTO_UPDATE | ✅ Current | Oct 15, 2025 | Backend |
| 10_TROUBLESHOOTING | ✅ Current | Oct 16, 2025 | All |

**All documentation verified and current!** ✅

---

## 🎯 Common Tasks

### New to the Project?
→ Read [00_START_HERE.md](00_START_HERE.md)

### Need to Call the API?
→ Read [02_API_DOCUMENTATION.md](02_API_DOCUMENTATION.md)

### Building a UI?
→ Read [04_FRONTEND_GUIDE.md](04_FRONTEND_GUIDE.md)

### Deploying to Production?
→ Read [05_DEPLOYMENT_GUIDE.md](05_DEPLOYMENT_GUIDE.md)

### Something Broken?
→ Read [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md)

---

## 📦 Archive

Historical documentation (76 files) preserved in `archive/`:
- Project status updates
- Implementation summaries
- Test results
- Legacy guides
- Historical fixes

**These are not maintained but preserved for reference.**

---

## 🎉 Recent Updates

### October 16, 2025
- ✅ Fixed 127,199 orphaned courses (56% of database!)
- ✅ Created 07_COURSE_FIX_COMPLETE.md
- ✅ Created 08_LIVE_PRICES.md
- ✅ Created 10_TROUBLESHOOTING.md
- ✅ Consolidated 88 markdown files → 11 core docs
- ✅ Archived 76 outdated files

### October 15, 2025
- ✅ Sporting Life V2 integration complete
- ✅ Racing Post completely removed
- ✅ Updated all core documentation

---

## 🚦 Project Status

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Database:** 226,465 races (2006-2025)  
**API Endpoints:** 45+  
**Test Coverage:** 97%  
**Documentation:** ✅ Complete

---

## 📞 Support

### Documentation Issues
- Check [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md)
- Search `archive/` for historical context
- Check inline code comments

### Code Comments
- All functions have doc comments
- Complex logic explained inline
- See `backend-api/internal/` directories

---

**Welcome to GiddyUp! Happy coding! 🏇🚀**
