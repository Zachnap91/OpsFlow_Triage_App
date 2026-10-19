import type { Category, Priority, RequestDetail, RequestItem, Stats, Status } from './types'

const json = async <T>(response: Response): Promise<T> => {
  if (!response.ok) throw new Error((await response.json()).detail ?? 'Request failed')
  return response.json()
}
export const getRequests = () => fetch('/api/requests').then(r => json<RequestItem[]>(r))
export const getStats = () => fetch('/api/stats').then(r => json<Stats>(r))
export const getRequest = (id:number) => fetch(`/api/requests/${id}`).then(r => json<RequestDetail>(r))
export const createRequest = (payload:{title:string;description:string;requester:string;department:string}) =>
  fetch('/api/requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>json<RequestItem>(r))
export const approveTriage = (id:number,category:Category,priority:Priority) =>
  fetch(`/api/requests/${id}/approve-triage`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category,priority,actor:'Portfolio Reviewer'})}).then(r=>json<RequestItem>(r))
export const updateRequest = (id:number,payload:{status?:Status;owner?:string}) =>
  fetch(`/api/requests/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,actor:'Portfolio Reviewer'})}).then(r=>json<RequestItem>(r))

