export const environment = {
  production: false,
  apiUrl: 'http://localhost:5001', // URL do servidor central
  //apiUrl: 'http://backend:5001', // URL do backend local
  endpoints: {
    votar: '/votar',
    resultados: '/resultados',
    candidatos: '/candidatos',
    cadastrar: '/cadastrar',
    electionalternative: '/electionalternative'
  }
}; 