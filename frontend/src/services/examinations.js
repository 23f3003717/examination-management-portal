import {api} from './api'; export const getExaminations=params=>api.get('/examinations',{params})
