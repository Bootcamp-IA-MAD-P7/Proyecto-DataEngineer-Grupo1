export interface LocationResult {
  full_name: string | null;
  city: string | null;
  address: string | null;
  ip_v4: string | null;
}

export interface ProfessionalProfileResult {
  full_name: string | null;
  company: string | null;
  company_address: string | null;
  company_email: string | null;
  company_telephone_number: string | null;
  job: string | null;
}

export interface PersonSearchResult {
  id: number;
  first_name: string | null;
  last_name: string | null;
  sex: string[] | null;
  telephone_number: string | null;
  email: string | null;
  passport: string | null;
  locations: LocationResult[];
  professional_profiles: ProfessionalProfileResult[];
}

export interface RowsPerTable {
  employees: number;
  locations: number;
  professional_profiles: number;
  bank_accounts: number;
  network_data: number;
  processing_audit: number;
}

export interface EmployeesMissingDomain {
  locations: number;
  professional_profiles: number;
  bank_accounts: number;
  network_data: number;
}

export interface StatisticsResult {
  rows_per_table: RowsPerTable;
  employees_missing_domain: EmployeesMissingDomain;
}
