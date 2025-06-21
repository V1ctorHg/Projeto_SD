export const environment = {
  production: false,
  apiUrl: '/api', // Aponta para o reverse proxy do Nginx
  //apiUrl: 'http://backend:5001', // URL do backend local
  endpoints: {
    votar: '/votar',
    resultados: '/resultados',
    candidatos: '/candidatos',
    cadastrar: '/cadastrar',
    electionalternative: '/electionalternative'
  }
}; 