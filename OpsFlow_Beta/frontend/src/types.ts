export type Category = 'Safety' | 'IT' | 'Facilities' | 'People' | 'Supply Chain' | 'Quality' | 'Other'
export type Priority = 'Low' | 'Medium' | 'High' | 'Critical'
export type Status = 'New' | 'Under Review' | 'Approved' | 'In Progress' | 'Completed'

export interface RequestItem {
  id: number; title: string; description: string; requester: string; department: string
  category: Category; priority: Priority; status: Status; owner: string | null
  ai_summary: string | null; ai_category: Category | null; ai_priority: Priority | null
  ai_confidence: number | null; triage_provider: string | null; triage_approved: boolean
  created_at: string; updated_at: string
}
export interface Activity { id:number; action:string; actor:string; detail:string; created_at:string }
export interface RequestDetail extends RequestItem { activity: Activity[] }
export interface Stats { total:number; open:number; critical:number; pending_approval:number; by_status:Record<string,number> }

