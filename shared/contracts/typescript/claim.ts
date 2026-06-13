// Claim domain contracts
// Canonical definitions for claim data crossing layer boundaries.

export enum ClaimStatus {
  Open = "OPEN",
  InReview = "IN_REVIEW",
  Pending = "PENDING",
  Closed = "CLOSED",
  Denied = "DENIED",
}

export enum ClaimType {
  AutoLiability = "AUTO_LIABILITY",
  AutoPhysicalDamage = "AUTO_PHYSICAL_DAMAGE",
  PropertyDamage = "PROPERTY_DAMAGE",
  WorkersCompensation = "WORKERS_COMPENSATION",
  GeneralLiability = "GENERAL_LIABILITY",
  MedicalMalpractice = "MEDICAL_MALPRACTICE",
}

export enum RiskLevel {
  Low = "LOW",
  Medium = "MEDIUM",
  High = "HIGH",
}

export enum PartyRole {
  Insured = "INSURED",
  Claimant = "CLAIMANT",
  Attorney = "ATTORNEY",
  Witness = "WITNESS",
  Expert = "EXPERT",
}

export interface ClaimParty {
  partyId: string;
  role: PartyRole;
  name: string;
  contactPhone: string | null;
  contactEmail: string | null;
  representedBy: string | null; // attorney name if represented
}

export interface Coverage {
  coverageId: string;
  coverageType: string;
  limit: number;
  deductible: number;
  isApplicable: boolean;
}

export interface ClaimDocument {
  documentId: string;
  title: string;
  documentType: string;
  uploadedAt: string; // ISO 8601
  uploadedBy: string;
}

export interface ClaimNote {
  noteId: string;
  content: string;
  author: string;
  authoredAt: string; // ISO 8601
  isAiGenerated: boolean;
  approvedBy: string | null;
  approvedAt: string | null;
}

export interface Claim {
  claimId: string;
  claimNumber: string;
  status: ClaimStatus;
  type: ClaimType;
  riskLevel: RiskLevel;
  dateOfLoss: string;        // ISO 8601 date
  reportedAt: string;        // ISO 8601 datetime
  description: string;
  reserveAmount: number;
  paidAmount: number;
  parties: ClaimParty[];
  coverages: Coverage[];
  notes: ClaimNote[];
  documents: ClaimDocument[];
  litigationFlag: boolean;
  jurisdictionCode: string;
}

export interface ClaimListItem {
  claimId: string;
  claimNumber: string;
  status: ClaimStatus;
  type: ClaimType;
  riskLevel: RiskLevel;
  dateOfLoss: string;
  reserveAmount: number;
  primaryInsuredName: string;
}
