// EvidenceSource contract
// Represents a single piece of retrieved knowledge that grounded an AI response.
// Attached to summaries, conversation turns, and draft notes.

export enum SourceType {
  ClaimDocument = "CLAIM_DOCUMENT",    // Document attached to the claim
  KnowledgeBase = "KNOWLEDGE_BASE",    // Enterprise knowledge base article
  ClaimNote = "CLAIM_NOTE",            // Prior note on the claim
  PolicyDocument = "POLICY_DOCUMENT",  // Insurance policy language
  Regulation = "REGULATION",           // Regulatory requirement
}

export interface EvidenceSource {
  sourceId: string;
  sourceType: SourceType;
  title: string;
  excerpt: string;         // The specific passage that was used
  relevanceScore: number;  // 0.0 – 1.0, how relevant this chunk was
  documentId: string | null;
  pageReference: string | null; // e.g. "Page 4, Section 2.1"
  retrievedAt: string;     // ISO 8601
}
