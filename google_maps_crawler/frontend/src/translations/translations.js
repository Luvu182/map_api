export const translations = {
  en: {
    // Header
    title: 'US Roads & Businesses Explorer',
    language: 'Language',
    
    // Search
    searchPlaceholder: 'Search for roads...',
    search: 'Search',
    noResults: 'No results found',
    
    // Filters
    filters: 'Filters',
    state: 'State',
    selectState: 'Select State',
    allStates: 'All States',
    county: 'County',
    selectCounty: 'Select County',
    allCounties: 'All Counties',
    targetCity: 'Target City (346 cities >100k pop)',
    cities: 'cities',
    selectTargetCity: 'Select a target city',
    roadType: 'Road Type',
    selectRoadType: 'Select Road Type',
    allTypes: 'All Types',
    
    // Road Types
    roadTypes: {
      motorway: 'Motorway',
      trunk: 'Trunk Road',
      primary: 'Primary Road',
      secondary: 'Secondary Road',
      tertiary: 'Tertiary Road',
      residential: 'Residential Street',
      service: 'Service Road',
      unclassified: 'Unclassified'
    },
    
    // Results
    results: 'Results',
    showingResults: 'Showing {{count}} results',
    segments: 'segments',
    totalLength: 'Total length',
    km: 'km',
    
    // Crawl Control
    crawlControl: 'Crawl Control',
    apiKey: 'API Key',
    enterApiKey: 'Enter Google Maps API Key',
    saveApiKey: 'Save API Key',
    startCrawl: 'Start Crawl',
    stopCrawl: 'Stop Crawl',
    crawling: 'Crawling...',
    
    // Statistics
    statistics: 'Statistics',
    totalRoads: 'Total Roads',
    totalBusinesses: 'Total Businesses',
    lastUpdated: 'Last Updated',
    
    // Business Analysis
    businessPotential: 'Business Potential',
    score: 'Score',
    rating: 'Rating',
    excellent: 'Excellent',
    veryGood: 'Very Good',
    good: 'Good',
    fair: 'Fair',
    poor: 'Poor',
    veryPoor: 'Very Poor',
    
    // Loading/Error states
    loading: 'Loading...',
    error: 'Error',
    tryAgain: 'Try Again',
    
    // Crawl page specific
    findBusinesses: 'Find businesses along US roads using Google Maps. Focus on high-potential areas for better results.',
    quickTips: 'Quick Tips for Finding Businesses:',
    quickTipsList: [
      'Start with popular keywords: restaurant, store, pharmacy',
      'Focus on "Major Commercial Roads" and "Local Business Streets" for best results',
      'Roads named "Main Street", "Broadway", or with "Plaza/Center" often have more businesses',
      'Filter by minimum road length (2-10 km is optimal)'
    ],
    searchConfiguration: 'Search Configuration',
    businessTypeQuestion: 'What type of business are you looking for?',
    businessPlaceholder: 'e.g. restaurant, clothing store, pharmacy...',
    popularSearches: 'Popular searches:',
    searchRoads: 'Search Roads',
    showOnlyUncrawled: 'Show Only Uncrawled',
    minimumRoadLength: 'Minimum Road Length',
    roadTypes: 'Road Types',
    selectRoadTypes: 'Select road types to search',
    noRoadsFound: 'No roads found matching your search criteria',
    crawlSelected: 'Crawl Selected Roads',
    crawlAll: 'Crawl All',
    
    // Additional labels
    locationFilters: 'Location Filters',
    stateRequired: 'State',
    countyOptional: 'County (Optional)',
    selectAState: 'Select a state...',
    advancedFilters: 'Advanced Filters & Options',
    roadTypesPreselected: 'Road Types (Pre-selected for best results)',
    additionalFilters: 'Additional Filters',
    bestRoadTypes: 'Best Road Types for Businesses:',
    sortBy: 'Sort by',
    businessPotentialSort: 'Business Potential',
    roadName: 'Road Name',
    roadLength: 'Road Length',
    roadNameSort: 'Name',
    lengthSort: 'Length',
    typeSort: 'Type',
    
    // Business Density Filter
    businessDensityFilter: 'Business Density Filter',
    allRoads: 'All roads',
    highPotentialOnly: 'High potential only',
    mediumPotential: 'Medium potential',
    
    // Road Length Options
    anyLength: 'Any length',
    atLeast1km: 'At least 1 km',
    atLeast2km: 'At least 2 km (Recommended)',
    atLeast5km: 'At least 5 km',
    atLeast10km: 'At least 10 km',
    
    // Status Labels
    starting: 'Starting...',
    complete: 'Complete',
    processing: 'Processing',
    failed: 'Failed',
    notCrawled: 'Not Crawled',
    retry: 'Retry',
    crawl: 'Crawl',
    
    // Table Headers
    tableRoadName: 'Road Name',
    tableType: 'Type',
    tableBusinessPotential: 'Business Potential',
    tableLength: 'Length',
    tableLocation: 'Location',
    tableStatus: 'Status',
    tableAction: 'Action',
    route: 'Route',
    unnamedRoad: 'Unnamed Road',
    
    // Business Potential Levels
    veryHigh: 'Very High',
    high: 'High', 
    medium: 'Medium',
    low: 'Low',
    veryLow: 'Very Low',
    
    // Results Section
    roadsFound: 'Roads Found',
    in: 'in',
    showingPagination: 'Showing {{start}} to {{end}} of {{total}} roads',
    previous: 'Previous',
    next: 'Next',
    page: 'Page',
    of: 'of',
    
    // Summary Statistics
    totalRoads: 'Total Roads',
    completed: 'Completed',
    inProgress: 'In Progress',
    notCrawled: 'Not Crawled',
    
    // No Results Message
    noRoadsFound: 'No roads found matching your criteria',
    tryAdjustingFilters: 'Try adjusting your filters or search in a different area',
    
    // Analysis Button
    viewAnalysis: 'View analysis',
    
    // Pro Tips section
    proTips: 'Pro Tips for Better Results',
    bestRoadTypesForBusiness: 'Best Road Types for Businesses:',
    searchByRoadName: 'Search by Road Name',
    tipMainStreet: 'Tip: "Main Street" and "Broadway" typically have many businesses',
    
    // Road categories
    localBusinessStreets: 'Local Business Streets',
    localBusinessDesc: 'Main St, Broadway, downtown streets',
    majorCommercialRoads: 'Major Commercial Roads',
    majorCommercialDesc: 'Main arterials, State Routes',
    highwaysInterstates: 'Highways & Interstates',
    highwaysDesc: 'I-5, I-95, US highways',
    serviceAccessRoads: 'Service & Access Roads',
    serviceDesc: 'Mall access, parking lots',
    
    // Business potential levels
    veryHighPotential: 'very-high business potential',
    highPotential: 'high business potential',
    mediumPotential: 'medium business potential',
    lowPotential: 'low business potential',
    veryLowPotential: 'very low business potential',
    
    // Pro Tips Content
    proTipsContent: {
      bestRoadTypes: [
        'Primary/Secondary roads in downtown areas',
        'Residential streets named "Main" or "Broadway"',
        'Roads near shopping centers or plazas'
      ],
      highDensityAreas: [
        'California: Los Angeles, San Francisco counties',
        'Texas: Harris (Houston), Dallas counties',
        'New York: New York, Kings counties'
      ]
    },
    highDensityBusinessAreas: 'High-Density Business Areas:',
    
    // Login
    login: {
      title: 'Login',
      subtitle: 'US Roads & Businesses Explorer',
      username: 'Username',
      password: 'Password',
      loginButton: 'Login',
      loggingIn: 'Logging in...',
      fillAllFields: 'Please fill in all fields',
      invalidCredentials: 'Invalid username or password',
      loginError: 'Login error. Please try again.',
      logout: 'Logout'
    }
  },
  
  vi: {
    // Header
    title: 'Khám phá Đường phố & Doanh nghiệp Hoa Kỳ',
    language: 'Ngôn ngữ',
    
    // Search
    searchPlaceholder: 'Nhập tên đường để tìm...',
    search: 'Tìm kiếm',
    noResults: 'Không tìm thấy kết quả nào',
    
    // Filters
    filters: 'Lọc theo',
    state: 'Bang',
    selectState: 'Chọn bang',
    allStates: 'Tất cả các bang',
    county: 'Quận',
    selectCounty: 'Chọn quận',
    allCounties: 'Tất cả các quận',
    targetCity: 'Thành phố mục tiêu (346 thành phố >100k dân)',
    cities: 'thành phố',
    selectTargetCity: 'Chọn thành phố mục tiêu',
    roadType: 'Phân loại đường',
    selectRoadType: 'Chọn loại đường',
    allTypes: 'Mọi loại đường',
    
    // Road Types
    roadTypes: {
      motorway: 'Xa lộ liên bang',
      trunk: 'Quốc lộ chính',
      primary: 'Đường chính',
      secondary: 'Đường phụ',
      tertiary: 'Đường nhánh',
      residential: 'Đường khu dân cư',
      service: 'Đường nội bộ',
      unclassified: 'Chưa phân loại'
    },
    
    // Results
    results: 'Kết quả tìm kiếm',
    showingResults: 'Đang hiển thị {{count}} kết quả',
    segments: 'đoạn đường',
    totalLength: 'Tổng chiều dài',
    km: 'km',
    
    // Crawl Control
    crawlControl: 'Tìm kiếm Doanh nghiệp',
    apiKey: 'Mã API',
    enterApiKey: 'Nhập mã API của Google Maps',
    saveApiKey: 'Lưu mã API',
    startCrawl: 'Bắt đầu tìm',
    stopCrawl: 'Dừng lại',
    crawling: 'Đang tìm kiếm...',
    
    // Statistics
    statistics: 'Thống kê',
    totalRoads: 'Tổng số đường',
    totalBusinesses: 'Doanh nghiệp đã tìm',
    lastUpdated: 'Cập nhật gần nhất',
    
    // Business Analysis
    businessPotential: 'Tiềm năng kinh doanh',
    score: 'Điểm số',
    rating: 'Xếp hạng',
    excellent: 'Rất cao',
    veryGood: 'Cao',
    good: 'Khá',
    fair: 'Trung bình',
    poor: 'Thấp',
    veryPoor: 'Rất thấp',
    
    // Loading/Error states
    loading: 'Đang tải...',
    error: 'Lỗi',
    tryAgain: 'Thử lại',
    
    // Crawl page specific
    findBusinesses: 'Khám phá các doanh nghiệp dọc theo đường phố Hoa Kỳ qua Google Maps. Hãy chọn khu vực sầm uất để có nhiều kết quả hơn.',
    quickTips: 'Mẹo hay:',
    quickTipsList: [
      'Thử với từ khóa quen thuộc: nhà hàng, shop, hiệu thuốc',
      'Ưu tiên "Đường thương mại" và "Đường dân sinh" sẽ cho nhiều kết quả',
      'Những con đường tên "Main Street", "Broadway", hay có chữ "Plaza/Center" thường đông doanh nghiệp',
      'Chọn đường dài từ 2-10km sẽ hiệu quả nhất'
    ],
    searchConfiguration: 'Thiết lập tìm kiếm',
    businessTypeQuestion: 'Bạn muốn tìm loại hình gì?',
    businessPlaceholder: 'VD: nhà hàng, quán ăn, shop thời trang, tiệm thuốc...',
    popularSearches: 'Hay tìm nhất:',
    searchRoads: 'Tìm đường',
    showOnlyUncrawled: 'Chỉ xem đường chưa tìm',
    minimumRoadLength: 'Độ dài tối thiểu',
    roadTypes: 'Kiểu đường',
    selectRoadTypes: 'Chọn kiểu đường muốn tìm',
    noRoadsFound: 'Không có đường nào phù hợp với yêu cầu',
    crawlSelected: 'Tìm các đường đã chọn',
    crawlAll: 'Tìm tất cả',
    
    // Additional labels
    locationFilters: 'Chọn vị trí',
    stateRequired: 'Bang',
    countyOptional: 'Quận (không bắt buộc)',
    selectAState: 'Chọn một bang...',
    advancedFilters: 'Tùy chọn nâng cao',
    roadTypesPreselected: 'Kiểu đường (đã chọn sẵn loại tốt nhất)',
    additionalFilters: 'Bộ lọc thêm',
    bestRoadTypes: 'Loại đường tốt nhất cho doanh nghiệp:',
    sortBy: 'Sắp xếp theo',
    businessPotentialSort: 'Tiềm năng kinh doanh',
    roadName: 'Tên đường',
    roadLength: 'Độ dài đường',
    roadNameSort: 'Tên',
    lengthSort: 'Độ dài',
    typeSort: 'Loại',
    
    // Business Density Filter
    businessDensityFilter: 'Lọc theo mật độ kinh doanh',
    allRoads: 'Tất cả các đường',
    highPotentialOnly: 'Chỉ tiềm năng cao',
    mediumPotential: 'Tiềm năng trung bình',
    
    // Road Length Options
    anyLength: 'Mọi độ dài',
    atLeast1km: 'Ít nhất 1 km',
    atLeast2km: 'Ít nhất 2 km (Khuyên dùng)',
    atLeast5km: 'Ít nhất 5 km',
    atLeast10km: 'Ít nhất 10 km',
    
    // Status Labels
    starting: 'Đang bắt đầu...',
    complete: 'Hoàn thành',
    processing: 'Đang xử lý',
    failed: 'Thất bại',
    notCrawled: 'Chưa tìm',
    retry: 'Thử lại',
    crawl: 'Tìm kiếm',
    
    // Table Headers
    tableRoadName: 'Tên đường',
    tableType: 'Loại',
    tableBusinessPotential: 'Tiềm năng kinh doanh',
    tableLength: 'Độ dài',
    tableLocation: 'Vị trí',
    tableStatus: 'Trạng thái',
    tableAction: 'Thao tác',
    route: 'Tuyến',
    unnamedRoad: 'Đường chưa đặt tên',
    
    // Business Potential Levels
    veryHigh: 'Rất cao',
    high: 'Cao', 
    medium: 'Trung bình',
    low: 'Thấp',
    veryLow: 'Rất thấp',
    
    // Results Section
    roadsFound: 'đường được tìm thấy',
    in: 'ở',
    showingPagination: 'Hiển thị {{start}} đến {{end}} trong tổng số {{total}} đường',
    previous: 'Trước',
    next: 'Tiếp',
    page: 'Trang',
    of: 'trên',
    
    // Summary Statistics
    totalRoads: 'Tổng số đường',
    completed: 'Đã hoàn thành',
    inProgress: 'Đang xử lý',
    notCrawled: 'Chưa tìm',
    
    // No Results Message
    noRoadsFound: 'Không tìm thấy đường nào phù hợp',
    tryAdjustingFilters: 'Hãy thử điều chỉnh bộ lọc hoặc tìm ở khu vực khác',
    
    // Analysis Button
    viewAnalysis: 'Xem phân tích',
    
    // Pro Tips section
    proTips: 'Mẹo để có kết quả tốt hơn',
    bestRoadTypesForBusiness: 'Loại đường tốt nhất cho kinh doanh:',
    searchByRoadName: 'Tìm theo tên đường',
    tipMainStreet: 'Mẹo: Đường "Main Street" và "Broadway" thường có nhiều doanh nghiệp',
    
    // Road categories
    localBusinessStreets: 'Đường phố kinh doanh',
    localBusinessDesc: 'Main St, Broadway, khu trung tâm',
    majorCommercialRoads: 'Đường thương mại chính',
    majorCommercialDesc: 'Đường chính, đường bang',
    highwaysInterstates: 'Xa lộ & Liên bang',
    highwaysDesc: 'I-5, I-95, xa lộ Mỹ',
    serviceAccessRoads: 'Đường dịch vụ & nội bộ',
    serviceDesc: 'Lối vào mall, bãi đậu xe',
    
    // Business potential levels
    veryHighPotential: 'tiềm năng rất cao',
    highPotential: 'tiềm năng cao',
    mediumPotential: 'tiềm năng trung bình',
    lowPotential: 'tiềm năng thấp',
    veryLowPotential: 'tiềm năng rất thấp',
    
    // County/State suffixes
    county: 'Quận',
    state: 'Bang',
    
    // Pro Tips Content
    proTipsContent: {
      bestRoadTypes: [
        'Đường chính Primary/Secondary ở khu trung tâm',
        'Đường dân cư tên "Main" hoặc "Broadway"',
        'Đường gần trung tâm mua sắm hoặc plaza'
      ],
      highDensityAreas: [
        'California: Quận Los Angeles, San Francisco',
        'Texas: Quận Harris (Houston), Dallas',
        'New York: Quận New York, Kings'
      ]
    },
    highDensityBusinessAreas: 'Khu vực đông doanh nghiệp:',
    
    // Login
    login: {
      title: 'Đăng nhập',
      subtitle: 'Khám phá Đường phố & Doanh nghiệp Hoa Kỳ',
      username: 'Tên đăng nhập',
      password: 'Mật khẩu',
      loginButton: 'Đăng nhập',
      loggingIn: 'Đang đăng nhập...',
      fillAllFields: 'Vui lòng điền đầy đủ thông tin',
      invalidCredentials: 'Tên đăng nhập hoặc mật khẩu không đúng',
      loginError: 'Lỗi đăng nhập. Vui lòng thử lại.',
      logout: 'Đăng xuất'
    }
  }
};

// Helper function to get translation
export const t = (key, language = 'en', replacements = {}) => {
  const keys = key.split('.');
  let value = translations[language];
  
  for (const k of keys) {
    value = value?.[k];
    if (!value) break;
  }
  
  // Fallback to English if translation not found
  if (!value && language !== 'en') {
    value = translations.en;
    for (const k of keys) {
      value = value?.[k];
      if (!value) break;
    }
  }
  
  // Replace placeholders like {{count}}
  if (typeof value === 'string') {
    Object.entries(replacements).forEach(([key, val]) => {
      value = value.replace(new RegExp(`{{${key}}}`, 'g'), val);
    });
  }
  
  return value || key;
};