<?php

namespace AppBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

class SearchController extends Controller
{
    /**
     * @param Request $request
     * 
     * @Route("/search", name="search")
     */
    public function research(Request $request)
    {
        $words = $request->request->get('words');
        
        $similaritiesJson = shell_exec();
        return new Response($similaritiesJson);
    }
}
