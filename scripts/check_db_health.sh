#!/bin/bash
# Database health check script

echo "╔══════════════════════════════════════════╗"
echo "║        Database Health Check             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check if container is running
if ! docker ps | grep -q roads-postgres; then
    echo "❌ ERROR: PostgreSQL container is not running!"
    echo "   Run: docker-compose up -d"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Database size
echo "📊 Database Size:"
docker exec roads-postgres psql -U postgres -d roads_db -t -c "SELECT pg_database_size('roads_db')/1024/1024 || ' MB' as size;"

# Table sizes
echo -e "\n📋 Top 5 Table Sizes:"
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    CASE 
        WHEN tablename = 'roads' THEN '5.2M road segments'
        WHEN tablename = 'businesses' THEN 'Google Maps data'
        WHEN tablename = 'crawl_status' THEN 'Crawl tracking'
        ELSE ''
    END as description
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 5;"

# Connection stats
echo -e "\n🔌 Connection Statistics:"
docker exec roads-postgres psql -U postgres -d roads_db -t -c "
SELECT 
    'Active: ' || COUNT(*) FILTER (WHERE state = 'active') || 
    ', Idle: ' || COUNT(*) FILTER (WHERE state = 'idle') ||
    ', Total: ' || COUNT(*)
FROM pg_stat_activity 
WHERE datname = 'roads_db';"

# Road statistics
echo -e "\n🛣️  Road Statistics:"
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT 
    COUNT(*) as total_roads,
    COUNT(CASE WHEN fullname IS NOT NULL THEN 1 END) as named_roads,
    COUNT(CASE WHEN fullname IS NULL THEN 1 END) as unnamed_roads,
    ROUND(100.0 * COUNT(CASE WHEN fullname IS NOT NULL THEN 1 END) / COUNT(*), 1) as named_percentage
FROM roads;"

# Road types breakdown
echo -e "\n🏷️  Road Types (MTFCC):"
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT 
    COALESCE(m.feature_class, 'Unknown') as road_type,
    r.mtfcc,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM roads r
LEFT JOIN mtfcc_descriptions m ON r.mtfcc = m.mtfcc
GROUP BY r.mtfcc, m.feature_class
ORDER BY count DESC
LIMIT 10;"

# Crawl status
echo -e "\n🕷️  Crawl Status:"
docker exec roads-postgres psql -U postgres -d roads_db -t -c "
SELECT 
    'Completed: ' || COUNT(*) FILTER (WHERE status = 'completed') ||
    ', Processing: ' || COUNT(*) FILTER (WHERE status = 'processing') ||
    ', Failed: ' || COUNT(*) FILTER (WHERE status = 'failed')
FROM crawl_status;"

# Index usage
echo -e "\n📈 Most Used Indexes:"
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans_count
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC
LIMIT 5;"

# Slow queries (if pg_stat_statements is enabled)
echo -e "\n🐌 Slow Query Check:"
docker exec roads-postgres psql -U postgres -d roads_db -t -c "
SELECT CASE 
    WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') 
    THEN 'pg_stat_statements enabled - monitor slow queries'
    ELSE 'pg_stat_statements not enabled - consider enabling for query monitoring'
END;" 2>/dev/null || echo "Query monitoring not configured"

echo -e "\n✨ Health check completed!"